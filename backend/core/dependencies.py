from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import oauth2_scheme, verify_token
from backend.dao.holder import HolderDAO
from backend.models.user import User
from backend.schemas.token import TokenPayload
from backend.services.auth import AuthService
from backend.services.otp_sending import MockOTPSendingService
from backend.services.user import UserService


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


async def get_current_user(
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    token: str = Depends(oauth2_scheme),
) -> User:
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

    phone_number: str = token_data.sub
    user = await dao.user.get_by_phone_number(db, phone_number=phone_number)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(
        get_current_active_user
    ),  # Зависит от активного пользователя
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


async def get_current_user_from_cookie(
    request: Request,  # Для доступа к cookie
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> Optional[User]:
    token = request.cookies.get("access_token")  # Имя вашего cookie
    if not token:
        return None

    if token.lower().startswith("bearer "):
        token = token.split(" ")[1]

    token_data: Optional[TokenPayload] = verify_token(token)
    if token_data is None or token_data.sub is None:
        return None  # Не кидаем ошибку, т.к. пользователь может быть не залогинен на странице

    phone_number: str = token_data.sub
    user = await dao.user.get_by_phone_number(db, phone_number=phone_number)
    return user


async def get_current_active_user_from_cookie(
    current_user: Optional[User] = Depends(get_current_user_from_cookie),
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authenticated",
            headers={"Location": "/login"},  # Редирект на страницу логина
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user. Please verify your account.",
        )
    return current_user


def get_otp_sending_service() -> MockOTPSendingService:
    return MockOTPSendingService()


def get_user_service() -> UserService:
    return UserService()


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
) -> AuthService:
    return AuthService(
        user_service=user_service, otp_sending_service=otp_sending_service
    )
