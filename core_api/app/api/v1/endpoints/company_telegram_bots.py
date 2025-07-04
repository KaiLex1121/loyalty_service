from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_bot_service,
    get_dao,
    get_owned_bot,
    get_owned_company,
    get_session,
)
from app.core.settings import AppSettings, get_settings
from app.dao.holder import HolderDAO
from app.models.company import Company
from app.models.telegram_bot import TelegramBot
from app.schemas.telegram_bot import (
    TelegramBotCreate,
    TelegramBotResponse,
    TelegramBotUpdate,
)
from app.services.telegram_bot import TelegramBotService
from app.services.telegram_integration import TelegramIntegrationService

router = APIRouter()


@router.post(
    "",
    response_model=TelegramBotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bot for a company",
)
async def create_bot(
    bot_in: TelegramBotCreate,
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    """
    Создает нового бота, привязанного к компании.
    Устанавливает вебхук в Telegram перед сохранением.
    """
    new_bot = await bot_service.create_bot(session, bot_data=bot_in)
    return new_bot


@router.get(
    "", response_model=List[TelegramBotResponse], summary="List bots for a company"
)
async def list_bots(
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    """Возвращает список всех ботов, привязанных к компании."""
    bots = await bot_service.get_bots_for_company(session, company_id=company.id)
    return bots


@router.patch(
    "/{bot_id}", response_model=TelegramBotResponse, summary="Update a bot's status"
)
async def update_bot(
    update_data: TelegramBotUpdate,
    db_bot: TelegramBot = Depends(get_owned_bot),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    """Обновляет бота (например, активирует/деактивирует)."""
    updated_bot = await bot_service.update_bot(
        session, db_bot=db_bot, update_data=update_data
    )
    return updated_bot


@router.delete(
    "/{bot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bot",
)
async def delete_bot(
    db_bot: TelegramBot = Depends(get_owned_bot),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    """Удаляет бота и его вебхук в Telegram."""
    await bot_service.delete_bot(session, db_bot=db_bot)
    return None
