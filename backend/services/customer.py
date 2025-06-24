# backend/services/customer_profile.py
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.db import session
from backend.models.account import Account
from backend.models.customer_role import CustomerRole
from backend.schemas.customer_role import CustomerRoleUpdate

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
