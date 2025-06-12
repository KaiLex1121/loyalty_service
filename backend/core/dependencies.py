from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.logger import get_logger
from backend.core.security import oauth2_scheme, verify_token
from backend.core.settings import AppSettings, get_settings
from backend.dao.holder import HolderDAO
from backend.enums.back_office import UserAccessLevelEnum
from backend.models.account import Account
from backend.models.company import Company
from backend.models.subscription import Subscription
from backend.models.user_role import UserRole
from backend.services.account import AccountService
from backend.services.auth import AuthService
from backend.services.company import CompanyService
from backend.services.dashboard import DashboardService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService

logger = get_logger(__name__)


async def get_session(request: Request):
    pool = request.app.state.pool
    async with pool() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_dao(request: Request) -> HolderDAO:
    dao = request.app.state.dao
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
    async with session.begin():
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
    async with session.begin():
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
    current_account: Account = Depends(get_current_account_with_profiles),
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
    company_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
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


def get_otp_sending_service() -> MockOTPSendingService:
    return MockOTPSendingService()


def get_account_service() -> AccountService:
    return AccountService()


def get_otp_code_service() -> OtpCodeService:
    return OtpCodeService()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


def get_company_service() -> CompanyService:
    return CompanyService()


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
