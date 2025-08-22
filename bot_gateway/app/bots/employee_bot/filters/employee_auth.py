from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Union
from aiogram.fsm.context import FSMContext

from app.bots.employee_bot.states.general import EmployeeAuthStates
from shared.enums.telegram_bot_enums import BotTypeEnum


class EmployeeAuthFilter(BaseFilter):
    """
    Проверяет, является ли пользователь аутентифицированным сотрудником.
    """

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        return data.get("is_authenticated") is True