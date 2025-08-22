import os
from typing import List

from app.core.dependencies import get_dao, get_session, verify_internal_api_key
from app.core.settings import settings
from app.dao.holder import HolderDAO
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.schemas import BotInfo

router = APIRouter()


@router.get(
    "/active",
    response_model=List[BotInfo],
    dependencies=[Depends(verify_internal_api_key)],
    summary="Get all active bots for gateway startup",
)
async def get_active_bots(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    """Возвращает список всех активных ботов для инициализации шлюза."""
    bots = await dao.telegram_bot.get_all_active_with_company(session)
    return [
        BotInfo(
            token=bot.token,
            company_id=bot.company_id,
            company_name=bot.company.name,
            bot_type=bot.bot_type,
        )
        for bot in bots
    ]
