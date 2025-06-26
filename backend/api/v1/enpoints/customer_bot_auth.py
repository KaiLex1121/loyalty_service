from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    authenticate_bot_and_get_company_id,
    get_client_onboarding_service,
    get_session,
)
from backend.schemas.customer_auth import (
    ClientTelegramOnboardingRequest,
    CustomerProfileResponse,
)
from backend.schemas.token import TokenResponse
from backend.services.customer_auth import CustomerAuthService

router = APIRouter()


@router.post(
    "/auth/telegram",  # Путь относительно префикса, который будет задан этому роутеру
    response_model=CustomerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Регистрация или вход клиента через Telegram",
    description="Принимает номер телефона и Telegram ID от Telegram-бота. "
    "Создает или находит аккаунт и профиль клиента, возвращает JWT-токен.",
)
async def onboard_telegram_client_endpoint(
    onboarding_data: ClientTelegramOnboardingRequest,
    service: CustomerAuthService = Depends(get_client_onboarding_service),
    session: AsyncSession = Depends(get_session),
    bot_company_id: int = Depends(authenticate_bot_and_get_company_id),
):
    customer_role = await service.onboard_telegram_client(
        session, onboarding_data, target_company_id=bot_company_id
    )

    return customer_role
