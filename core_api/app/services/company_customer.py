# backend/services/customer_profile.py
from decimal import Decimal

from app.dao.holder import HolderDAO
from app.db import session
from app.models.account import Account
from app.models.customer_role import CustomerRole
from app.schemas.customer_role import CustomerRoleUpdate
from sqlalchemy.ext.asyncio import AsyncSession

# from backend.schemas.customer_role import CustomerRoleUpdate # Если будет обновление профиля
# from backend.schemas.account import AccountUpdate # Если будет обновление данных Account через этот профиль
# from backend.core.logger import get_logger
# logger = get_logger(__name__)


class CustomerService:

    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def get_customer_profile(
        self,
        customer_role: CustomerRole,  # Приходит из зависимости get_current_customer_role
    ) -> CustomerRole:  # Возвращаем модель, API преобразует в CustomerProfileResponse
        return customer_role

    async def get_customer_balance(
        self,
        customer_role: CustomerRole,
    ) -> CustomerRole:
        return customer_role
