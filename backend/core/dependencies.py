from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import oauth2_scheme, verify_token
from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.schemas.token import TokenPayload
from backend.services.account import AccountService
from backend.services.auth import AuthService
from backend.services.company import CompanyService
from backend.services.dashboard import DashboardService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService


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


def get_jinja_templates(request: Request) -> Jinja2Templates:
    templates_instance = request.app.state.templates
    return templates_instance


async def get_current_account_with_profiles(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    token: str = Depends(oauth2_scheme),
) -> Account:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data: Optional[TokenPayload] = verify_token(token)
    if token_data is None or token_data.sub is None:
        raise credentials_exception

    account_id = int(token_data.sub)

    account = await dao.account.get_by_id_with_profiles(session, id_=account_id)

    if account is None:
        raise credentials_exception
    return account


async def get_current_active_account_with_profiles(
    current_account: Account = Depends(get_current_account_with_profiles),
) -> Account:

    if not current_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return current_account


@lru_cache
def get_otp_sending_service() -> MockOTPSendingService:
    return MockOTPSendingService()


@lru_cache
def get_account_service() -> AccountService:
    return AccountService()


@lru_cache
def get_otp_code_service() -> OtpCodeService:
    return OtpCodeService()


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService()


@lru_cache
def get_company_service() -> CompanyService:
    return CompanyService()


@lru_cache
def get_auth_service(
    account_service: AccountService = Depends(get_account_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
    otp_code_service: OtpCodeService = Depends(get_otp_code_service),
) -> AuthService:
    return AuthService(
        account_service=account_service,
        otp_sending_service=otp_sending_service,
        otp_code_service=otp_code_service,
    )
