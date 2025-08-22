# from typing import Callable, Dict, Any, Awaitable
# from aiogram import BaseMiddleware
# from aiogram.types import TelegramObject, Message

# from app.core.settings import settings
# from shared.utils.security import verify_token

# class AuthMiddleware(BaseMiddleware):
#     """
#     Проверяет JWT-токен сотрудника перед выполнением защищенных хендлеров.
#     """
#     async def __call__(
#         self,
#         handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
#         event: TelegramObject,
#         data: Dict[str, Any]
#     ) -> Any:

#         # Это middleware должно работать только для Message, не для всех апдейтов
#         if not isinstance(event, Message):
#             return await handler(event, data)

#         state = data.get("state")
#         if not state:
#             return await handler(event, data)

#         user_data = await state.get_data()
#         jwt_token = user_data.get("jwt_token")

#         if not jwt_token:
#             if event.text != "/start":
#                 await event.answer("Пожалуйста, авторизуйтесь для доступа к этой функции. Поделитесь номером повторно")
#                 return
#             return await handler(event, data)

#         payload = verify_token(token=jwt_token, secret_key=settings.SECURITY.JWT_SECRET_KEY, algorithm=settings.SECURITY.ALGORITHM)
#         if not payload:
#             await state.clear() # Очищаем сессию
#             await event.answer("Ваша сессия истекла. Пожалуйста, войдите снова. Отправьте /start.")
#             return

#         # Если токен валиден, обогащаем контекст данными из него
#         data["employee_id"] = int(payload.sub)
#         data["token_payload"] = payload

#         return await handler(event, data)