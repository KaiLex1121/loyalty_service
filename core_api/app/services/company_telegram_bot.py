from typing import List
from urllib.parse import urljoin
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.dao.holder import HolderDAO
from app.exceptions.common import ConflictException
from app.models.telegram_bot import TelegramBot
from app.schemas.company_telegram_bot import TelegramBotCreate, TelegramBotCreateInternal, TelegramBotUpdate
from app.publishers import bot_management_events_publisher # Импортируем наш экземпляр брокера
from shared.schemas.schemas import BotManagementEvent # Импортируем общую схему для события

class TelegramBotService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    def _get_webhook_url_for_bot(self, token: str) -> str:
        """
        Формирует полный URL для вебхука, на который Bot Gateway будет принимать обновления.
        """
        # GATEWAY_BASE_URL - это публичный адрес нашего bot_gateway из .env
        path = f"/telegram/bot{token}"
        return urljoin(settings.API.GATEWAY_BASE_URL, path)

    async def create_bot(self, session: AsyncSession, bot_data: TelegramBotCreate, company_id: int) -> TelegramBot:
        """
        Создает нового бота или восстанавливает существующего.
        Обрабатывает конфликты с мягко удаленными записями.
        """
        # --- Сценарий 1: Пользователь пытается добавить бота с уже существующим токеном ---
        soft_deleted_bot = await self.dao.telegram_bot.find_soft_deleted_by_token(
            session, token=bot_data.token
        )

        if soft_deleted_bot:
            # Если бот найден, но принадлежит другой компании - это ошибка.
            if soft_deleted_bot.company_id != company_id:
                raise ConflictException(
                    "This bot token was previously used by another company and cannot be reused."
                )

            # Если бот принадлежит этой же компании, восстанавливаем его.
            print(f"Restoring soft-deleted bot ID {soft_deleted_bot.id} with token ...{bot_data.token[-4:]}")
            restored_bot = await self.dao.telegram_bot.restore_bot(session, db_bot=soft_deleted_bot)

            # Публикуем событие 'bot_activated' (или 'bot_created', в зависимости от семантики)
            event = BotManagementEvent(
                event_type="bot_activated", # Восстановление - это как активация
                token=restored_bot.token,
                webhook_url=self._get_webhook_url_for_bot(restored_bot.token)
            )
            await bot_management_events_publisher.publish(event)
            print(f"Published 'bot_activated' event for restored bot ID {restored_bot.id}")

            return restored_bot

        # --- Сценарий 2: Конфликт по ТИПУ бота ---
        # Эта проверка теперь игнорирует мягко удаленных ботов благодаря изменениям в DAO.
        exists = await self.dao.telegram_bot.check_bot_type_exists_for_company(
            session, company_id=company_id, bot_type=bot_data.bot_type
        )
        if exists:
            raise ConflictException(
                f"An active bot of type '{bot_data.bot_type.value}' already exists for this company."
            )

        # --- Сценарий 3: Создание полностью нового бота ---
        print(f"Creating a new bot for company {company_id} with token ...{bot_data.token[-4:]}")
        bot_internal_schema = TelegramBotCreateInternal(
            **bot_data.model_dump(),
            company_id=company_id
        )

        new_bot = await self.dao.telegram_bot.create(session, obj_in=bot_internal_schema)
        await session.flush()

        event = BotManagementEvent(
            event_type="bot_created",
            token=new_bot.token,
            webhook_url=self._get_webhook_url_for_bot(new_bot.token)
        )

        await bot_management_events_publisher.publish(event)
        print(f"Published 'bot_created' event for new bot ID {new_bot.id}")

        return new_bot


    async def get_bots_for_company(self, session: AsyncSession, company_id: int) -> List[TelegramBot]:
        """Возвращает список ботов для указанной компании."""
        return await self.dao.telegram_bot.get_by_company_id(session, company_id=company_id)

    async def update_bot(self, session: AsyncSession, db_bot: TelegramBot, update_data: TelegramBotUpdate) -> TelegramBot:
        """
        Обновляет бота в БД и публикует событие, если его статус активности изменился.
        """
        original_status = db_bot.is_active

        updated_bot = await self.dao.telegram_bot.update(session, db_obj=db_bot, obj_in=update_data)
        await session.flush()

        event_type = None
        if original_status is True and updated_bot.is_active is False:
            event_type = "bot_deactivated"
        elif original_status is False and updated_bot.is_active is True:
            event_type = "bot_activated"

        # Если статус активности изменился, публикуем событие
        if event_type:
            event = BotManagementEvent(
                event_type=event_type,
                token=updated_bot.token,
                webhook_url=self._get_webhook_url_for_bot(updated_bot.token)
            )
            await bot_management_events_publisher.publish(event)
            print(f"Published '{event_type}' event for bot ID {updated_bot.id}")

        return updated_bot

    async def delete_bot(self, session: AsyncSession, db_bot: TelegramBot) -> TelegramBot:
        """
        Мягко удаляет бота из БД и публикует событие 'bot_deleted'.
        """
        # Сохраняем токен перед удалением, так как объект может стать недействительным
        bot_token = db_bot.token
        bot_id = db_bot.id

        # Используем мягкое удаление
        deleted_bot = await self.dao.telegram_bot.soft_delete(session, id_=bot_id)

        if deleted_bot:
            # Формируем и публикуем событие
            event = BotManagementEvent(
                event_type="bot_deleted",
                token=bot_token,
                webhook_url=None # URL не нужен для удаления
            )
            await bot_management_events_publisher.publish(event)
            print(f"Published 'bot_deleted' event for bot ID {bot_id}")

        return deleted_bot