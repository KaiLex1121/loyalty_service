from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.states.general import OnboardingDialogStates
from app.core.settings import settings

from shared.utils.security import verify_token


class AuthMiddleware(BaseMiddleware):
    """
    Проверяет JWT-токен сотрудника перед выполнением защищенных хендлеров.
    Работает как с обычными сообщениями (Message), так и с нажатиями
    на инлайн-кнопки (CallbackQuery).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        state = data.get("state")
        if not state:
            return await handler(event, data)

        user_data = await state.get_data()
        jwt_token = user_data.get("jwt_token")

        # --- Сценарий 1: Пользователь не авторизован (нет токена) ---
        if not jwt_token:
            current_state = await state.get_state()
            is_allowed_unauthenticated_action = False
            is_start_command = event.message.text == "/start"
            is_in_auth_flow = current_state in [
                OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION,
            ]
            is_contact_sharing = event.message.contact is not None

            is_allowed_unauthenticated_action = (
                is_start_command or is_in_auth_flow or is_contact_sharing
            )
            # Если действие не разрешено, блокируем его.
            if not is_allowed_unauthenticated_action:
                await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
                await event.message.answer(
                    "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона.",
                    reply_markup=OnboardingKeyboards.share_contact_keyboard,
                )
                return
            # Если действие разрешено (это /start или контакт), просто пропускаем дальше.
            return await handler(event, data)

        # --- Сценарий 2: Токен есть, проверяем его валидность ---
        payload = verify_token(
            token=jwt_token,
            secret_key=settings.SECURITY.JWT_SECRET_KEY,
            algorithm=settings.SECURITY.ALGORITHM,
        )

        if not payload:
            # Токен невалиден или просрочен

            await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
            await event.message.answer(
                "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона.",
                reply_markup=OnboardingKeyboards.share_contact_keyboard,
            )
            return

        # --- Сценарий 3: Успешная авторизация ---
        data["employee_id"] = int(payload.sub)
        data["token_payload"] = payload

        return await handler(event, data)
