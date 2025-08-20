from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDAO
from app.core.dependencies import get_dao, get_owned_bot, get_owned_company, get_session
from app.models.company import Company
from app.models.telegram_bot import TelegramBot
from app.schemas.company_telegram_bot import TelegramBotCreate, TelegramBotResponse, TelegramBotUpdate
from app.services.company_telegram_bot import TelegramBotService

router = APIRouter()

def get_bot_service(dao: HolderDAO = Depends(get_dao)) -> TelegramBotService:
    return TelegramBotService(dao=dao)

@router.post("", response_model=TelegramBotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_in: TelegramBotCreate,
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    new_bot = await bot_service.create_bot(session, bot_data=bot_in, company_id=company.id)
    return new_bot

@router.get("", response_model=List[TelegramBotResponse])
async def list_bots(
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    return await bot_service.get_bots_for_company(session, company_id=company.id)

@router.put("/{bot_id}", response_model=TelegramBotResponse)
async def update_bot(
    update_data: TelegramBotUpdate,
    db_bot: TelegramBot = Depends(get_owned_bot),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    return await bot_service.update_bot(session, db_bot=db_bot, update_data=update_data)

@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    db_bot: TelegramBot = Depends(get_owned_bot),
    session: AsyncSession = Depends(get_session),
    bot_service: TelegramBotService = Depends(get_bot_service),
):
    await bot_service.delete_bot(session, db_bot=db_bot)
    return None