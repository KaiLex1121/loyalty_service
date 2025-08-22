from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Union

from shared.enums.telegram_bot_enums import BotTypeEnum


class BotTypeFilter(BaseFilter):
    """
    Фильтр проверяет, соответствует ли тип текущего бота
    одному из разрешённых типов.
    """
    def __init__(self, bot_type: Union[BotTypeEnum, list[BotTypeEnum]]):
        if isinstance(bot_type, list):
            self.bot_types = bot_type
        else:
            self.bot_types = [bot_type]

    async def __call__(self, event: Message, **data) -> bool:
        # data приходит распакованным (middleware кладёт туда значения)
        bot_type: BotTypeEnum = data.get("bot_type")

        if not bot_type:
            return False

        return bot_type in self.bot_types
