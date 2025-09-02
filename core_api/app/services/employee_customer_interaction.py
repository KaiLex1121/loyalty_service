import datetime
import decimal
from typing import Optional, Tuple

from app.core.security import (
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    verify_otp_hash,
)
from app.core.settings import AppSettings
from app.dao.holder import HolderDAO

# Кастомные исключения
from app.enums.auth_enums import OtpPurposeEnum
from app.enums.loyalty_enums import TransactionStatusEnum, TransactionTypeEnum
from app.exceptions.common import BadRequestException, ForbiddenException, NotFoundException
from app.exceptions.services.account import AccountInactiveException
from app.exceptions.services.backoffice_auth import (
    InvalidOTPException,
    OTPExpiredException,
    OTPNotFoundException,
    OTPSendingException,
)
from app.exceptions.services.company_customer import (  # Создайте эти исключения
    CustomerNotFoundByPhoneInCompanyException,
)
from app.exceptions.services.employee_customer_interaction import (
    CashbackAccrualFailedException,
    InsufficientCashbackBalanceException,
    InvalidSpendAmountException,
)
from app.models.customer_role import CustomerRole  # То, что мы ищем
from app.models.employee_role import EmployeeRole
from app.models.transaction import Transaction
from app.schemas.otp_code import OtpCodeCreate
from app.schemas.transaction import TransactionCreateInternal
from app.services.otp_code import OtpCodeService
from app.services.otp_sending import (  # Для контекста сотрудника
    MockOTPSendingService,
)
from app.services.transaction_cashback_calculation import CashbackCalculationService
from sqlalchemy.ext.asyncio import AsyncSession

# from backend.core.logger import get_logger
# logger = get_logger(__name__)


class EmployeeCustomerInteractionService:
    def __init__(
        self,
        dao: HolderDAO,
        settings: AppSettings,
        cashback_calculation_service: CashbackCalculationService,
        otp_code_service: OtpCodeService,
        otp_sending_service: MockOTPSendingService,
    ):
        self.dao = dao
        self.cashback_calculation_service = cashback_calculation_service
        self.otp_code_service = otp_code_service
        self.settings = settings
        self.otp_sending_service = otp_sending_service

    async def _get_customer_role_for_operation(
        self, session: AsyncSession, customer_phone_number: str, company_id: int
    ) -> CustomerRole:
        """Вспомогательный метод для получения CustomerRole по номеру телефона в компании."""
        customer_role = await self.dao.customer_role.find_by_customer_phone_and_company_id_with_details(
            session, customer_phone_number=customer_phone_number, company_id=company_id
        )
        if not customer_role:
            raise CustomerNotFoundByPhoneInCompanyException(
                phone_number=customer_phone_number, company_id=company_id
            )
        if not customer_role.account or not customer_role.account.is_active:
            raise AccountInactiveException(account_id=customer_role.account_id)
        return customer_role

    def _mask_phone_number(self, phone_number: str) -> str:
        """Маскирует номер телефона, оставляя первые и последние цифры."""
        if len(phone_number) > 7:
            return f"{phone_number[:4]}***{phone_number[-3:]}"
        return phone_number

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

    async def accrue_cashback_for_customer(
        self,
        session: AsyncSession,
        acting_employee_role: EmployeeRole,
        purchase_amount: decimal.Decimal,
        customer_role_id: int, # <-- ИЗМЕНЕНИЕ: принимаем ID, а не номер телефона
        outlet_id: int, # <-- ИЗМЕНЕНИЕ: делаем outlet_id обязательным
    ) -> Transaction:
        """
        Выполняет начисление кэшбэка клиенту от имени сотрудника.
        """
        # 1. Получаем профиль клиента по ID
        target_customer_role = await self.dao.customer_role.get_active_by_id_with_account(
            session, id_=customer_role_id
        )
        if not target_customer_role:
            raise NotFoundException(f"Active customer profile with ID {customer_role_id} not found.")

        # 2. Проверяем, что сотрудник и клиент из одной компании
        if acting_employee_role.company_id != target_customer_role.company_id:
            raise ForbiddenException("Employee and customer do not belong to the same company.")

        # 3. Проверяем, что торговая точка принадлежит компании сотрудника
        #    (эта проверка может быть избыточной, если outlet_id берется из токена, но так надежнее)
        outlet = await self.dao.outlet.get_active(session, id_=outlet_id)
        if not outlet or outlet.company_id != acting_employee_role.company_id:
            raise ForbiddenException(f"Outlet with ID {outlet_id} not found or does not belong to the company.")

        # 4. Вызываем сервис расчета кэшбэка (эта часть не меняется)
        transaction, _promo_usage = (
            await self.cashback_calculation_service.calculate_and_record_cashback_for_purchase(
                session=session,
                company=acting_employee_role.company,
                customer_role=target_customer_role,
                purchase_amount=purchase_amount,
                outlet_id=outlet_id,
                performed_by_employee_role_id=acting_employee_role.id,
            )
        )

        if not transaction:
            raise CashbackAccrualFailedException(
                detail="Cashback accrual resulted in zero amount. No transaction created."
            )

        return transaction


    async def request_spend_otp(
        self,
        session: AsyncSession,
        acting_employee_role: EmployeeRole,
        customer_phone_number: str,
        purchase_amount: decimal.Decimal,
    ) -> Tuple[
        decimal.Decimal, str
    ]:  # Возвращает сумму к списанию и маскированный телефон
        """
        Рассчитывает сумму списания, генерирует и отправляет OTP клиенту.
        """

        target_customer_role = await self._get_customer_role_for_operation(
            session, customer_phone_number, acting_employee_role.company_id
        )

        if acting_employee_role.company_id != target_customer_role.company_id:
            raise PermissionError(
                "Сотрудник и клиент должны принадлежать одной компании."
            )

        if purchase_amount <= 0:
            raise InvalidSpendAmountException(
                detail="Сумма покупки для списания кэшбэка должна быть больше нуля."
            )

        current_balance = target_customer_role.cashback_balance
        if current_balance <= 0:
            raise InsufficientCashbackBalanceException(
                current_balance=current_balance,
                detail="На балансе клиента нет средств для списания.",
            )

        amount_to_spend = min(current_balance, purchase_amount)

        # Генерация и сохранение OTP
        otp_purpose = OtpPurposeEnum.TRANSACTION_CONFIRMATION
        customer_account = target_customer_role.account

        await self.otp_code_service.invalidate_previous_otps(
            session, self.dao, customer_account, otp_purpose
        )

        plain_otp = generate_otp(self.settings)
        hashed_otp = get_otp_hash(plain_otp, self.settings)
        otp_expires_at = get_otp_expiry_time(self.settings)

        otp_schema = OtpCodeCreate(
            hashed_code=hashed_otp,
            expires_at=otp_expires_at,
            purpose=otp_purpose,
            account_id=customer_account.id,
            channel="customer_sms",
        )
        await self.otp_code_service.create_otp(session, self.dao, otp_schema)

        # Отправка OTP клиенту
        otp_sent = await self.otp_sending_service.send_otp(
            phone_number=customer_account.phone_number, otp_code=plain_otp
        )
        if not otp_sent:
            raise OTPSendingException(
                internal_details={"phone_number": customer_account.phone_number}
            )

        masked_phone = self._mask_phone_number(customer_account.phone_number)
        return amount_to_spend, masked_phone

    async def confirm_spend_with_otp(
        self,
        session: AsyncSession,
        acting_employee_role: EmployeeRole,
        customer_phone_number: str,
        otp_code: str,
        purchase_amount: decimal.Decimal,  # Сумма покупки нужна для создания транзакции
        outlet_id: Optional[int] = None,
    ) -> Transaction:
        """
        Проверяет OTP и выполняет списание кэшбэка.
        """

        target_customer_role = await self._get_customer_role_for_operation(
            session, customer_phone_number, acting_employee_role.company_id
        )

        if acting_employee_role.company_id != target_customer_role.company_id:
            raise PermissionError(
                "Сотрудник и клиент должны принадлежать одной компании."
            )

        customer_account = target_customer_role.account
        otp_purpose = OtpPurposeEnum.TRANSACTION_CONFIRMATION

        # Проверка OTP
        active_otp = await self.dao.otp_code.get_active_otp_by_account_and_purpose(
            session=session, account_id=customer_account.id, purpose=otp_purpose
        )
        if not active_otp:
            raise OTPNotFoundException(
                internal_details={
                    "account_id": customer_account.id,
                    "purpose": otp_purpose.value,
                }
            )
        if active_otp.is_expired:
            raise OTPExpiredException(
                internal_details={
                    "account_id": customer_account.id,
                    "otp_id": active_otp.id,
                    "expires_at": active_otp.expires_at.isoformat(),
                }
            )

        if not verify_otp_hash(
            otp_code=otp_code,
            hashed_otp_code=active_otp.hashed_code,
            settings=self.settings,
        ):
            raise InvalidOTPException(
                internal_details={
                    "account_id": customer_account.id,
                    "otp_id": active_otp.id,
                }
            )
        await self.otp_code_service.set_mark_otp_as_used(session, self.dao, active_otp)

        # Повторно рассчитываем сумму списания и проверяем баланс на случай,
        # если баланс изменился между запросом OTP и подтверждением.
        amount_to_spend = min(target_customer_role.cashback_balance, purchase_amount)
        if amount_to_spend <= 0:
            raise InsufficientCashbackBalanceException(
                current_balance=target_customer_role.cashback_balance,
                detail="На балансе клиента больше нет средств для списания.",
            )

        # Обновляем баланс и создаем транзакцию
        target_customer_role.cashback_balance -= amount_to_spend
        session.add(target_customer_role)

        transaction_data = TransactionCreateInternal(
            company_id=acting_employee_role.company_id,
            customer_role_id=target_customer_role.id,
            outlet_id=outlet_id,
            transaction_type=TransactionTypeEnum.SPENDING_PURCHASE,
            status=TransactionStatusEnum.COMPLETED,
            purchase_amount=purchase_amount,
            cashback_spent=amount_to_spend,
            balance_after=target_customer_role.cashback_balance,
            transaction_time=datetime.datetime.now(datetime.timezone.utc),
            description=f"Списание кэшбэка в счет покупки на сумму {purchase_amount}.",
            cashback_accrued=decimal.Decimal("0.00"),
            performed_by_employee_id=acting_employee_role.id,
        )
        new_transaction = await self.dao.transaction.create(
            session, obj_in=transaction_data
        )

        await session.flush()
        await session.refresh(new_transaction)

        return new_transaction
