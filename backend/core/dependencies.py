from curses.ascii import US
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
from backend.enums.back_office import UserAccessLevelEnum
from backend.exceptions.common import UnauthorizedException
from backend.exceptions.services.outlet import OutletNotFoundException
from backend.models.account import Account
from backend.models.company import Company
from backend.models.outlet import Outlet
from backend.models.subscription import Subscription
from backend.models.user_role import UserRole
from backend.services.account import AccountService
from backend.services.auth import AuthService
from backend.services.company import CompanyService
from backend.services.dashboard import DashboardService
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
        selectinload(Company.cashback),
        selectinload(Company.subscriptions).options(
            selectinload(Subscription.tariff_plan)
        ),
    )

    result = await session.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or you do not have permission to access it.",
        )

    return company


async def get_verified_outlet_for_user(
    # outlet_id берется из параметра пути с тем же именем (тот, что в эндпоинте)
    outlet_id: int,
    session: AsyncSession = Depends(get_session),
    current_user_role: UserRole = Depends(
        get_current_user_profile_from_account
    ),  # Получаем UserRole текущего пользователя
    dao: HolderDAO = Depends(get_dao),
) -> Outlet:
    """
    1. Находит активную (не мягко удаленную) торговую точку по ID.
    2. Проверяет, имеет ли текущий аутентифицированный пользователь (UserRole)
       право доступа к этой торговой точке (через владение родительской компанией
       или если он FULL_SYSTEM_ADMIN).
    3. Возвращает объект OutletModel, если все проверки пройдены.
    4. Выбрасывает OutletNotFoundException или AuthorizationException в случае неудачи.
    """

    # 1. Найти активную торговую точку
    # Метод get_active из CRUDBase для OutletDAO уже проверяет deleted_at.is_(None)
    outlet = await dao.outlet.get_active(session, id_=outlet_id)
    if not outlet:
        raise OutletNotFoundException(identifier=outlet_id)

    # 2. Проверить права доступа
    user_has_access = False

    # 2.1. Проверка на FULL_SYSTEM_ADMIN
    if current_user_role.access_level == UserAccessLevelEnum.FULL_ADMIN:
        user_has_access = True
    else:
        # 2.2. Проверка, является ли пользователь владельцем компании, к которой принадлежит ТТ
        if current_user_role.companies_owned:
            for owned_company in current_user_role.companies_owned:
                if (
                    owned_company.id == outlet.company_id
                    and not owned_company.is_deleted
                ):
                    user_has_access = True
                    break

    if not user_has_access:
        raise UnauthorizedException(
            detail=f"You do not have permission to access outlet ID {outlet_id}."
        )

    return outlet


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
