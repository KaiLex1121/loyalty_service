from typing import List, Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.enums.telegram_bot_enums import BotTypeEnum
from app.models.telegram_bot import TelegramBot
from app.schemas.telegram_bot import (  # Эти схемы Pydantic нужно будет создать
    TelegramBotCreate,
    TelegramBotUpdate,
)


class TelegramBotDAO(BaseDAO[TelegramBot, TelegramBotCreate, TelegramBotUpdate]):
    def __init__(self):
        super().__init__(TelegramBot)

    async def get_by_token(
        self, session: AsyncSession, *, token: str
    ) -> Optional[TelegramBot]:
        stmt = select(self.model).where(self.model.token == token)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_company_id(
        self, session: AsyncSession, *, company_id: int
    ) -> List[TelegramBot]:
        stmt = select(self.model).where(self.model.company_id == company_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_company_id(
        self, session: AsyncSession, *, bot_id: int, company_id: int
    ) -> Optional[TelegramBot]:
        stmt = select(self.model).where(
            self.model.id == bot_id, self.model.company_id == company_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def check_bot_type_exists_for_company(
        self, session: AsyncSession, *, company_id: int, bot_type: BotTypeEnum
    ) -> bool:
        stmt = select(self.model.id).where(
            self.model.company_id == company_id, self.model.bot_type == bot_type
        )
        result = await session.execute(select(exists(stmt)))
        return result.scalar_one()

    async def get_all_active_with_company(self, session: AsyncSession) -> List[Bot]:
        """
        Получает список всех активных ботов (не удаленных и с флагом is_active=True)
        и жадно подгружает связанную информацию о компании для каждого бота.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.is_active.is_(True)
            )
            .options(
                selectinload(self.model.company) # Жадная загрузка связанной компании
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_company_and_type(
        self, session: AsyncSession, *, company_id: int, bot_type: BotTypeEnum
    ) -> Optional[TelegramBot]:
        """
        Находит активного бота по ID компании и его типу (клиентский или для сотрудников).
        Используется для поиска нужного бота для рассылок или других операций.
        """
        stmt = select(self.model).where(
            self.model.company_id == company_id,
            self.model.bot_type == bot_type,
            self.model.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalars().first()
