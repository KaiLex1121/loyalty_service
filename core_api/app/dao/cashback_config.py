from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.models.promotions.cashback_config import CashbackConfig
from app.schemas.promotion_cashback_config import (  # Предполагаем схему
    CashbackConfigCreate,
    CashbackConfigUpdate,
)


class CashbackConfigDAO(
    BaseDAO[CashbackConfig, CashbackConfigCreate, CashbackConfigUpdate]
):
    def __init__(self):
        super().__init__(CashbackConfig)
