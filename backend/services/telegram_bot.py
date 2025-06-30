from typing import List
from urllib.parse import urljoin

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.settings import AppSettings
from backend.dao.holder import HolderDAO
from backend.exceptions.common import ConflictException
from backend.models.telegram_bot import TelegramBot
from backend.schemas.telegram_bot import TelegramBotCreate, TelegramBotUpdate
from backend.services.telegram_integration import TelegramIntegrationService


class TelegramBotService:
    def __init__(
        self,
        dao: HolderDAO,
        settings: AppSettings,
        telegram_service: TelegramIntegrationService,
    ):
        self.dao = dao
        self.settings = settings
        self.telegram_service = telegram_service

    def _get_webhook_url_for_bot(self, token: str) -> str:
        """Формирует полный URL для вебхука."""
        # Пример пути: /api/v1/webhook/telegram/bot<TOKEN>
        path = f"/api/v1/webhook/telegram/bot{token}"
        # Предполагаем, что в настройках есть базовый URL нашего сервиса
        return urljoin(self.settings.API.SERVER_BASE_URL, path)

    async def create_bot(
        self, session: AsyncSession, *, bot_data: TelegramBotCreate
    ) -> TelegramBot:
        # Проверяем, что у компании еще нет бота такого типа
        exists = await self.dao.telegram_bot.check_bot_type_exists_for_company(
            session, company_id=bot_data.company_id, bot_type=bot_data.bot_type
        )
        if exists:
            raise ConflictException(
                f"A bot of type '{bot_data.bot_type.value}' already exists for this company."
            )

        # Устанавливаем вебхук ПЕРЕД сохранением в БД для консистентности
        webhook_url = self._get_webhook_url_for_bot(bot_data.token)
        await self.telegram_service.set_webhook(
            bot_token=bot_data.token, webhook_url=webhook_url
        )

        # Если вебхук установлен успешно, создаем бота в БД
        new_bot = await self.dao.telegram_bot.create(session, obj_in=bot_data)
        return new_bot

    async def get_bots_for_company(
        self, session: AsyncSession, *, company_id: int
    ) -> List[TelegramBot]:
        return await self.dao.telegram_bot.get_by_company_id(
            session, company_id=company_id
        )

    async def update_bot(
        self,
        session: AsyncSession,
        *,
        db_bot: TelegramBot,
        update_data: TelegramBotUpdate,
    ) -> TelegramBot:
        # Если бот деактивируется, удаляем вебхук
        if update_data.is_active is False and db_bot.is_active is True:
            await self.telegram_service.delete_webhook(bot_token=db_bot.token)
        # Если бот активируется, устанавливаем вебхук
        elif update_data.is_active is True and db_bot.is_active is False:
            webhook_url = self._get_webhook_url_for_bot(db_bot.token)
            await self.telegram_service.set_webhook(
                bot_token=db_bot.token, webhook_url=webhook_url
            )

        return await self.dao.telegram_bot.update(
            session, db_obj=db_bot, obj_in=update_data
        )

    async def delete_bot(
        self, session: AsyncSession, *, db_bot: TelegramBot
    ) -> TelegramBot:
        # Удаляем вебхук перед удалением из БД
        await self.telegram_service.delete_webhook(bot_token=db_bot.token)
        await self.dao.telegram_bot.hard_delete(session, id_=db_bot.id)
        return db_bot
