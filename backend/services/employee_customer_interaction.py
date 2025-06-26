# backend/services/employee_customer_interaction.py
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO

# Кастомные исключения
from backend.exceptions.services.customer import (  # Создайте эти исключения
    CustomerNotFoundByPhoneInCompanyException,
)
from backend.models.customer_role import CustomerRole  # То, что мы ищем
from backend.models.employee_role import EmployeeRole  # Для контекста сотрудника

# from backend.core.logger import get_logger
# logger = get_logger(__name__)


class EmployeeCustomerInteractionService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def find_customer_by_phone_for_employee(
        self,
        session: AsyncSession,
        customer_phone_number: str,
        acting_employee_role: EmployeeRole,  # Аутентифицированный сотрудник
    ) -> CustomerRole:
        """
        Ищет CustomerRole по номеру телефона клиента в той же компании,
        к которой принадлежит действующий сотрудник.
        """
        target_company_id = acting_employee_role.company_id

        customer_role = await self.dao.customer_role.find_by_customer_phone_and_company_id_with_details(
            session,
            customer_phone_number=customer_phone_number,
            company_id=target_company_id,
        )

        if not customer_role:
            # logger.warning(f"Клиент с номером телефона {customer_phone_number} не найден в компании ID {target_company_id}.")
            raise CustomerNotFoundByPhoneInCompanyException(
                phone_number=customer_phone_number, company_id=target_company_id
            )

        if not customer_role.account or not customer_role.account.is_active:
            # logger.warning(f"Найден CustomerRole ID {customer_role.id}, но связанный Account ID {customer_role.account_id} неактивен.")
            # Можно либо вернуть как есть, либо выбросить ошибку, если сотрудник не должен видеть неактивных.
            # Для поиска обычно лучше вернуть, а операции (начисление/списание) уже будут проверять активность.
            # Но если это критично для отображения:
            # raise CustomerAccountInactiveException(account_id=customer_role.account_id)
            pass  # Пока просто ничего не делаем

        # logger.info(f"Найден CustomerRole ID {customer_role.id} (Account ID: {customer_role.account_id}) для компании {target_company_id}.")
        return customer_role

    # В будущем здесь могут быть методы для начисления/списания кэшбэка сотрудником:
    # async def accrue_cashback_by_employee(
    #     self,
    #     session: AsyncSession,
    #     acting_employee_role: EmployeeRole,
    #     target_customer_role: CustomerRole,
    #     purchase_amount: decimal.Decimal,
    #     # ... другие параметры ...
    # ):
    #     # Проверка, что target_customer_role принадлежит той же компании, что и acting_employee_role
    #     if acting_employee_role.company_id != target_customer_role.company_id:
    #         raise SomePermissionDeniedException("Сотрудник не может выполнять операции для клиентов другой компании.")
    #
    #     # Вызов CashbackCalculationService
    #     # cashback_service = CashbackCalculationService(self.dao) # Если создавать здесь
    #     # transaction, promo_usage = await cashback_service.calculate_and_record_cashback_for_purchase(...)
    #     pass

    # async def spend_cashback_by_employee(
    #     self,
    #     session: AsyncSession,
    #     acting_employee_role: EmployeeRole,
    #     target_customer_role: CustomerRole,
    #     amount_to_spend: decimal.Decimal,
    #     # ... другие параметры ...
    # ):
    #     # ... (проверка принадлежности компании) ...
    #     # ... (проверка баланса клиента) ...
    #     # ... (создание транзакции списания) ...
    #     # ... (обновление баланса клиента) ...
    #     pass
