from backend.dao.base import BaseDAO
from backend.models.cashback import Cashback
from backend.schemas.cashback import CashbackConfigCreate  # Предполагаем схему


class CashbackConfigDAO(
    BaseDAO[Cashback, CashbackConfigCreate, CashbackConfigCreate]
):
    def __init__(self):
        super().__init__(Cashback)
