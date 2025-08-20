from typing import List, Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.enums.telegram_bot_enums import BotTypeEnum
from app.models.telegram_bot import TelegramBot
from app.schemas.company_telegram_bot import (  # Эти схемы Pydantic нужно будет создать
    TelegramBotCreateInternal,
    TelegramBotUpdate,
)


class TelegramBotDAO(BaseDAO[TelegramBot, TelegramBotCreateInternal, TelegramBotUpdate]):
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

    async def find_soft_deleted_by_token(self, session: AsyncSession, token: str) -> Optional[TelegramBot]:
        """Находит мягко удаленного бота по токену."""
        stmt = select(self.model).where(
            self.model.token == token,
            self.model.deleted_at.is_not(None)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def check_bot_type_exists_for_company(self, session: AsyncSession, company_id: int, bot_type: BotTypeEnum) -> bool:
        """Проверяет существование АКТИВНОГО бота заданного типа для компании."""
        stmt = select(self.model.id).where(
            self.model.company_id == company_id,
            self.model.bot_type == bot_type,
            self.model.deleted_at.is_(None)
        )
        result = await session.execute(select(stmt.exists()))
        return result.scalar_one()

    async def restore_bot(self, session: AsyncSession, db_bot: TelegramBot) -> TelegramBot:
        """Восстанавливает мягко удаленного бота."""
        db_bot.deleted_at = None
        db_bot.is_active = True # При восстановлении всегда делаем его активным
        session.add(db_bot)
        await session.flush()
        await session.refresh(db_bot)
        return db_bot

    async def get_all_active_with_company(self, session: AsyncSession) -> List[TelegramBot]:
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
