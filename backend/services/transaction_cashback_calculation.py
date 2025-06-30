# backend/services/cashback_calculation.py
import datetime
import decimal
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.enums import (
    CashbackTypeEnum,
    PromotionTypeEnum,
    TransactionStatusEnum,
    TransactionTypeEnum,
)
from backend.models.company import Company
from backend.models.customer_role import CustomerRole
from backend.models.promotions.promotion import Promotion
from backend.models.promotions.promotion_usage import PromotionUsage
from backend.models.transaction import Transaction
from backend.schemas.promotion_usage import PromotionUsageCreateInternal
from backend.schemas.transaction import TransactionCreateInternal


class CashbackCalculationService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def calculate_and_record_cashback_for_purchase(
        self,
        session: AsyncSession,
        company: Company,
        customer_role: CustomerRole,
        purchase_amount: decimal.Decimal,
        performed_by_employee_role_id: int,
        outlet_id: int,
    ) -> Tuple[Optional[Transaction], Optional[PromotionUsage]]:
        """
        Рассчитывает кэшбэк (с учетом акций и базового), создает транзакцию,
        запись об использовании акции (если применимо) и обновляет баланс клиента.
        Возвращает созданную транзакцию и запись об использовании акции.
        """
        if purchase_amount <= decimal.Decimal("0"):
            return None, None

        current_time = datetime.datetime.now(datetime.timezone.utc)

        # Поиск применимой акции
        applied_promotion = await self._find_applicable_promotion(
            session, company.id, customer_role.id, purchase_amount, current_time
        )

        # Расчет кэшбэка
        final_cashback = await self._calculate_cashback(
            session, company.id, purchase_amount, applied_promotion
        )

        if final_cashback <= decimal.Decimal("0"):
            return None, None

        # Создание записей в БД
        return await self._create_transaction_records(
            session=session,
            company=company,
            customer_role=customer_role,
            purchase_amount=purchase_amount,
            cashback_amount=final_cashback,
            applied_promotion=applied_promotion,
            performed_by_employee_role_id=performed_by_employee_role_id,
            outlet_id=outlet_id,
            current_time=current_time,
        )

    async def _find_applicable_promotion(
        self,
        session: AsyncSession,
        company_id: int,
        customer_role_id: int,
        purchase_amount: decimal.Decimal,
        current_time: datetime.datetime,
    ) -> Optional[Promotion]:
        """Находит лучшую применимую акцию для покупки."""
        active_promotions = await self.dao.promotion.get_active_promotions_for_company(
            session, company_id=company_id, current_date=current_time
        )

        applicable_promotions = []

        for promotion in active_promotions:
            if promotion.promotion_type != PromotionTypeEnum.CASHBACK:
                continue

            if await self._can_apply_promotion(
                session, promotion, customer_role_id, purchase_amount
            ):
                # Рассчитываем потенциальный кэшбэк для сравнения
                potential_cashback = self._calculate_promotion_cashback_amount(
                    purchase_amount, promotion.cashback_config
                )
                applicable_promotions.append(
                    {
                        "promotion": promotion,
                        "potential_cashback": potential_cashback,
                        "priority": getattr(promotion, "priority", 0),
                    }
                )

        if not applicable_promotions:
            return None

        # Сортируем по приоритету (по убыванию), затем по размеру кэшбэка (по убыванию)
        applicable_promotions.sort(
            key=lambda x: (x["priority"], x["potential_cashback"]), reverse=True
        )

        best_promotion = applicable_promotions[0]["promotion"]
        return best_promotion

    async def _can_apply_promotion(
        self,
        session: AsyncSession,
        promotion: Promotion,
        customer_role_id: int,
        purchase_amount: decimal.Decimal,
    ) -> bool:
        """Проверяет, можно ли применить акцию."""
        # Проверка минимальной суммы покупки
        if (
            promotion.min_purchase_amount
            and purchase_amount < promotion.min_purchase_amount
        ):
            return False

        # Проверка общего лимита использований
        if (
            promotion.max_total_uses is not None
            and promotion.current_total_uses >= promotion.max_total_uses
        ):
            return False

        # Проверка лимита использований на клиента
        if promotion.max_uses_per_customer is not None:
            customer_uses = (
                await self.dao.promotion_usage.count_usages_by_customer_for_promotion(
                    session,
                    promotion_id=promotion.id,
                    customer_role_id=customer_role_id,
                )
            )
            if customer_uses >= promotion.max_uses_per_customer:
                return False

        return True

    async def _calculate_cashback(
        self,
        session: AsyncSession,
        company_id: int,
        purchase_amount: decimal.Decimal,
        applied_promotion: Optional[Promotion],
    ) -> decimal.Decimal:
        """Рассчитывает итоговый кэшбэк."""
        if applied_promotion and applied_promotion.cashback_config:
            return self._calculate_promotion_cashback(
                purchase_amount, applied_promotion.cashback_config
            )

        # Если акция не применилась, используем базовый кэшбэк
        return await self._calculate_base_cashback(session, company_id, purchase_amount)

    def _calculate_promotion_cashback(
        self, purchase_amount: decimal.Decimal, cashback_config
    ) -> decimal.Decimal:
        """Рассчитывает кэшбэк по акции."""
        if not cashback_config:
            return decimal.Decimal("0")

        return self._calculate_promotion_cashback_amount(
            purchase_amount, cashback_config
        )

    def _calculate_promotion_cashback_amount(
        self, purchase_amount: decimal.Decimal, cashback_config
    ) -> decimal.Decimal:
        """Вспомогательный метод для расчета кэшбэка по акции."""
        if not cashback_config:
            return decimal.Decimal("0")

        cashback_amount = decimal.Decimal("0")

        if (
            cashback_config.cashback_type == CashbackTypeEnum.PERCENTAGE
            and cashback_config.cashback_percentage is not None
        ):
            cashback_amount = (
                purchase_amount * cashback_config.cashback_percentage
            ) / decimal.Decimal("100")

        elif (
            cashback_config.cashback_type == CashbackTypeEnum.FIXED_AMOUNT
            and cashback_config.cashback_amount is not None
        ):
            cashback_amount = cashback_config.cashback_amount

        # Округление до 2 знаков после запятой
        cashback_amount = cashback_amount.quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )

        # Применение максимального лимита кэшбэка за транзакцию
        if cashback_config.max_cashback_per_transaction is not None:
            if cashback_config.max_cashback_per_transaction == decimal.Decimal("0"):
                # Если лимит = 0, считаем это как "без лимита"
                pass
            elif cashback_amount > cashback_config.max_cashback_per_transaction:
                cashback_amount = cashback_config.max_cashback_per_transaction

        return cashback_amount

    async def _calculate_base_cashback(
        self, session: AsyncSession, company_id: int, purchase_amount: decimal.Decimal
    ) -> decimal.Decimal:
        """Рассчитывает базовый кэшбэк компании."""
        base_config = (
            await self.dao.default_company_cashback_config.get_active_by_company_id(
                session, company_id=company_id
            )
        )

        if not base_config:
            return decimal.Decimal("0")

        if base_config.default_percentage <= decimal.Decimal("0"):
            return decimal.Decimal("0")

        cashback_amount = (
            purchase_amount * base_config.default_percentage
        ) / decimal.Decimal("100")

        final_amount = cashback_amount.quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )

        return final_amount

    async def _create_transaction_records(
        self,
        session: AsyncSession,
        company: Company,
        customer_role: CustomerRole,
        purchase_amount: decimal.Decimal,
        cashback_amount: decimal.Decimal,
        applied_promotion: Optional[Promotion],
        performed_by_employee_role_id: int,
        outlet_id: int,
        current_time: datetime.datetime,
    ) -> Tuple[Transaction, Optional[PromotionUsage]]:
        """Создает записи транзакции и использования акции."""
        # Обновление баланса клиента
        customer_role.cashback_balance += cashback_amount
        session.add(customer_role)

        # Создание транзакции
        transaction_data = TransactionCreateInternal(
            company_id=company.id,
            customer_role_id=customer_role.id,
            outlet_id=outlet_id,
            transaction_type=TransactionTypeEnum.ACCRUAL_PURCHASE,
            status=TransactionStatusEnum.COMPLETED,
            purchase_amount=purchase_amount,
            cashback_accrued=cashback_amount,
            cashback_spent=decimal.Decimal("0"),
            balance_after=customer_role.cashback_balance,
            transaction_time=current_time,
            description=None,
            performed_by_employee_id=performed_by_employee_role_id,
        )
        created_transaction = await self.dao.transaction.create(
            session, obj_in=transaction_data
        )

        created_promotion_usage = None
        if applied_promotion:
            # Создание записи об использовании акции
            promo_usage_data = PromotionUsageCreateInternal(
                promotion_id=applied_promotion.id,
                customer_role_id=customer_role.id,
                transaction_id=created_transaction.id,
                cashback_accrued=cashback_amount,
            )
            created_promotion_usage = await self.dao.promotion_usage.create(
                session, obj_in=promo_usage_data
            )

            # Увеличение счетчика использований акции
            await self.dao.promotion.increment_total_uses(
                session, promotion_id=applied_promotion.id
            )

        # Обновление объектов из БД
        await session.flush()
        await session.refresh(created_transaction)
        if created_promotion_usage:
            await session.refresh(created_promotion_usage)

        return created_transaction, created_promotion_usage
