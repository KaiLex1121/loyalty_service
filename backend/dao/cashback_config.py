from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.promotions.cashback_config import CashbackConfig
from backend.schemas.promotion_cashback_config import (  # Предполагаем схему
    CashbackConfigCreate,
    CashbackConfigUpdate,
)


class CashbackConfigDAO(
    BaseDAO[CashbackConfig, CashbackConfigCreate, CashbackConfigUpdate]
):
    def __init__(self):
        super().__init__(CashbackConfig)
