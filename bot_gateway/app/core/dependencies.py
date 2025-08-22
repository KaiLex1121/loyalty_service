from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.api_client import CoreApiClient  # Предполагаем, что он будет нужен
from app.config import JWT_ALGORITHM, JWT_SECRET_KEY

# Pydantic-модель для удобства, можно расширить
from pydantic import BaseModel

from shared.schemas import (
    TokenPayload,  # Предполагаем, что нужна будет модель сотрудника
)
from shared.utils.security import verify_token


class Employee(BaseModel):
    id: int
    # ... другие поля, если нужны: full_name, company_id и т.д.


async def get_current_employee(
    state: FSMContext, message: Message
) -> Optional[Employee]:
    """
    Aiogram Dependency. Проверяет JWT токен сотрудника из FSM-хранилища.

    - Если токен валиден, возвращает информацию о сотруднике.
    - Если токен отсутствует, просрочен или невалиден, очищает сессию
      и возвращает None.
    """
    user_data = await state.get_data()
    jwt_token = user_data.get("jwt_token")

    if not jwt_token:
        return None

    payload = verify_token(
        token=jwt_token, secret_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
    )

    if not payload:
        # Токен невалиден или просрочен
        await state.clear()
        await message.answer(
            "Ваша сессия истекла. Пожалуйста, войдите снова, поделившись номером."
        )
        return None

    # Токен валиден, возвращаем объект сотрудника
    return Employee(id=int(payload.sub))
