from backend.dao.base import CRUDBase
from backend.models.cashback import CashbackConfig
from backend.schemas.cashback import CashbackConfigCreate # Предполагаем схему

class CashbackConfigDAO(CRUDBase[CashbackConfig, CashbackConfigCreate, CashbackConfigCreate]):
    pass # Базовых методов CRUD должно хватить
