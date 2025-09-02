from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    Update,
    Message,
    CallbackQuery,
    TelegramObject,
)
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
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        bot_type = data.get("bot_type")
        if bot_type != "employee":
            return await handler(event, data)

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
            is_start_command = False
            is_in_auth_flow = current_state in [
                OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION,
                OnboardingDialogStates.WAITING_FOR_OUTLET_SELECTION,
            ]
            is_contact_sharing = False

            if isinstance(event, Update) and event.message:
                is_start_command = event.message.text == "/start"
                is_contact_sharing = event.message.contact is not None

            is_allowed_unauthenticated_action = (
                is_start_command or is_in_auth_flow or is_contact_sharing
            )

            if not is_allowed_unauthenticated_action:
                await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
                await self._send_auth_request(event)
                return

            return await handler(event, data)

        # --- Сценарий 2: Токен есть, проверяем его валидность ---
        payload = verify_token(
            token=jwt_token,
            secret_key=settings.SECURITY.JWT_SECRET_KEY,
            algorithm=settings.SECURITY.ALGORITHM,
        )

        if not payload:
            await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
            await state.update_data(jwt_token=None)
            await self._send_auth_request(event)
            return

        # --- Сценарий 3: Успешная авторизация ---
        data["employee_id"] = int(payload.sub)
        data["token_payload"] = payload

        return await handler(event, data)

    async def _send_auth_request(self, event: Update):
        """
        Унифицированная отправка сообщения пользователю в зависимости от типа апдейта.
        """
        text = "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона."

        if event.message:  # обычное сообщение
            await event.message.answer(text, reply_markup=OnboardingKeyboards.share_contact_keyboard)

        elif event.callback_query:  # колбэк-кнопка
            cq: CallbackQuery = event.callback_query
            if cq.message:
                await cq.message.answer(text, reply_markup=OnboardingKeyboards.share_contact_keyboard)
            else:
                # редкий случай: callback без message (inline-кнопки в другом чате)
                await cq.answer(text, show_alert=True)
