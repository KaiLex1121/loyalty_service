from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.logger import get_logger
from backend.core.security import oauth2_scheme, verify_token
from backend.core.settings import AppSettings, get_settings
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool
from backend.enums import UserAccessLevelEnum
from backend.exceptions.common import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from backend.exceptions.services.employee import EmployeeNotFoundException
from backend.exceptions.services.outlet import OutletNotFoundException
from backend.models.account import Account
from backend.models.company import Company
from backend.models.employee_role import EmployeeRole
from backend.models.outlet import Outlet
from backend.models.promotions.promotion import Promotion
from backend.models.subscription import Subscription
from backend.models.user_role import UserRole
from backend.services.account import AccountService
from backend.services.auth import AuthService
from backend.services.company import CompanyService
from backend.services.company_default_cashback_config import (
    CompanyDefaultCashbackConfigService,
)
from backend.services.dashboard import DashboardService
from backend.services.employee import EmployeeService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService
from backend.services.outlet import OutletService

logger = get_logger(__name__)


async def get_session(settings: AppSettings = Depends(get_settings)):
    session_maker = create_pool(settings)

    async with session_maker() as session:
        try:
            yield session
            await session.commit()

        except SQLAlchemyError as db_error:
            await session.rollback()
            logger.error(f"Database error, transaction rolled back: {db_error}")
            raise

        except Exception as general_error:
            await session.rollback()
            logger.error(f"General error, transaction rolled back: {general_error}")
            raise

        finally:
            await session.close()


async def get_dao() -> HolderDAO:
    dao = HolderDAO()
    return dao


async def get_account_id_from_token(
    token: str = Depends(oauth2_scheme),
    settings: AppSettings = Depends(get_settings),
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token=token, settings=settings)

    if token_data is None:
        raise credentials_exception
    try:
        account_id = int(token_data.sub)
        return account_id
    except (ValueError, TypeError):
        raise credentials_exception


async def get_current_account_without_relations(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    account_id: int = Depends(get_account_id_from_token),
) -> Optional[Account]:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    account = await dao.account.get_by_id_without_relations(session, id_=account_id)
    return account


async def get_current_active_account_without_relations(
    current_account: Account = Depends(get_current_account_without_relations),
) -> Account:

    if not current_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return current_account


async def get_current_account_with_profiles(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    account_id: int = Depends(get_account_id_from_token),
) -> Optional[Account]:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    account = await dao.account.get_by_id_with_profiles(session, id_=account_id)
    return account


async def get_current_active_account_with_profiles(
    current_account: Account = Depends(get_current_account_with_profiles),
) -> Account:

    if not current_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return current_account


async def get_current_user_profile_from_account(
    current_account: Account = Depends(get_current_active_account_with_profiles),
) -> UserRole:
    if current_account.user_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile required for this operation. Account does not have an user profile.",
        )
    return current_account.user_profile


async def get_current_full_system_admin(
    current_user_profile: UserRole = Depends(get_current_user_profile_from_account),
) -> UserRole:
    if current_user_profile.access_level != UserAccessLevelEnum.FULL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full system administrator privileges required.",
        )
    return current_user_profile


async def get_owned_company(
    # company_id берется из параметра пути с тем же именем (тот, что в эндпоинте)
    company_id: int,
    session: AsyncSession = Depends(get_session),
    current_user_role: UserRole = Depends(get_current_user_profile_from_account),
) -> Company:
    """
    Проверяет, имеет ли текущий пользователь (UserRole) доступ к запрашиваемой компании.
    Возвращает объект Company, если доступ разрешен.
    Загружает связанные сущности для ответа.
    """

    if current_user_role.access_level == UserAccessLevelEnum.FULL_ADMIN:
        stmt = select(Company).filter(
            Company.id == company_id, Company.deleted_at.is_(None)
        )
    else:  # Иначе, он должен быть владельцем
        stmt = select(Company).filter(
            Company.id == company_id,
            Company.owner_user_role_id == current_user_role.id,
            Company.deleted_at.is_(None),
        )

    stmt = stmt.options(
        selectinload(Company.owner_user_role),
        selectinload(Company.default_cashback_config),
        selectinload(Company.subscriptions).options(
            selectinload(Subscription.tariff_plan)
        ),
    )

    result = await session.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise NotFoundException(
            detail=f"Company with ID {company_id} not found or you do not have permission to access it.",
        )

    return company


async def get_verified_outlet_for_company(
    outlet_id: int,  # Из пути
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> Outlet:
    """
    Получает активную торговую точку (Outlet) по ID и проверяет,
    принадлежит ли она компании, к которой у текущего пользователя есть доступ
    (через зависимость get_owned_company).
    Возвращает объект Outlet, если все проверки пройдены.
    """
    outlet = await dao.outlet.get_active(session, id_=outlet_id)

    if not outlet:
        raise OutletNotFoundException(identifier=outlet_id)

    if outlet.company_id != company.id:
        raise NotFoundException(
            detail=f"Outlet with ID {outlet_id} not found in company {company.id}."
        )

    return outlet


async def get_owned_employee_role(
    employee_role_id: int,  # Из пути
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> EmployeeRole:
    """
    Получает EmployeeRole по ID и проверяет, принадлежит ли он компании,
    к которой у текущего пользователя есть доступ (через зависимость get_owned_company).
    Возвращает EmployeeRoleModel с загруженными account и assigned_outlets.
    """
    employee_role = await dao.employee_role.get_by_id_with_details(
        session, employee_role_id=employee_role_id
    )

    if not employee_role:
        raise EmployeeNotFoundException(identifier=employee_role_id)

    if employee_role.company_id != company.id:
        raise NotFoundException(
            detail=f"Employee with ID {employee_role_id} not found in company {company.id}."
        )

    return employee_role


def get_otp_sending_service() -> MockOTPSendingService:
    return MockOTPSendingService()


def get_account_service() -> AccountService:
    return AccountService()


def get_otp_code_service() -> OtpCodeService:
    return OtpCodeService()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


def get_outlet_service(
    dao: HolderDAO = Depends(get_dao),
) -> OutletService:
    return OutletService(dao=dao)


def get_company_service(
    settings: AppSettings = Depends(get_settings),
    dao: HolderDAO = Depends(get_dao),
) -> CompanyService:
    return CompanyService(settings=settings, dao=dao)


def get_employee_service(
    dao: HolderDAO = Depends(get_dao),
) -> EmployeeService:
    return EmployeeService(dao=dao)


def get_cashback_service(
    dao: HolderDAO = Depends(get_dao),
) -> CompanyDefaultCashbackConfigService:
    return CompanyDefaultCashbackConfigService(dao=dao)


def get_auth_service(
    account_service: AccountService = Depends(get_account_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
    otp_code_service: OtpCodeService = Depends(get_otp_code_service),
    settings: AppSettings = Depends(get_settings),
) -> AuthService:
    return AuthService(
        account_service=account_service,
        otp_sending_service=otp_sending_service,
        otp_code_service=otp_code_service,
        settings=settings,
    )
