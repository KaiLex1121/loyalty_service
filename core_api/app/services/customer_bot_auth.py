# backend/services/client_onboarding.py
import datetime
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.security import create_access_token
from app.core.settings import AppSettings
from app.dao.holder import HolderDAO
from app.exceptions.services.company_customer import (
    CompanyNotFoundForOnboardingException,
    CustomerOnboardingException,
    PhoneNumberAlreadyLinkedToDifferentTelegramException,
    TelegramIdConflictException,
)
from app.models.account import Account
from app.models.company import Company
from app.models.customer_role import CustomerRole
from app.schemas.account import (
    AccountCreateForClientOnboarding,
    AccountCreateInternal,
    AccountUpdate,
)
from app.schemas.customer_bot_auth import ClientTelegramOnboardingRequest
from app.schemas.customer_role import CustomerRoleCreateInternal

logger = get_logger(__name__)


class CustomerAuthService:
    def __init__(self, dao: HolderDAO, settings: AppSettings):
        self.dao = dao
        self.settings = settings

    async def _get_or_create_account(
        self, session: AsyncSession, data: ClientTelegramOnboardingRequest
    ) -> Account:
        """Находит или создает Account. Обновляет Telegram данные, если необходимо."""
        account_by_phone = await self.dao.account.get_by_phone_number_with_all_profiles(
            session, phone_number=data.phone_number
        )
        account_by_telegram_id = None
        if data.telegram_user_id:
            account_by_telegram_id = (
                await self.dao.account.get_by_telegram_id_with_all_profiles(
                    session, telegram_user_id=data.telegram_user_id
                )
            )

        if account_by_phone and account_by_telegram_id:
            if account_by_phone.id != account_by_telegram_id.id:
                raise PhoneNumberAlreadyLinkedToDifferentTelegramException(
                    phone_number=data.phone_number
                )
            # Это один и тот же аккаунт, все хорошо
            account = account_by_phone
        elif account_by_phone:  # Найден только по телефону
            account = account_by_phone
            if (
                data.telegram_user_id
                and account.telegram_user_id != data.telegram_user_id
            ):
                # Если у этого аккаунта уже есть TG ID, и он другой - конфликт
                if account.telegram_user_id is not None:
                    # logger.warning(f"Аккаунт {account.id} (тел {data.phone_number}) уже имеет TG ID {account.telegram_user_id}, попытка привязать {data.telegram_user_id}.")
                    raise TelegramIdConflictException(
                        telegram_id=data.telegram_user_id,
                        detail=f"Этот Telegram аккаунт уже связан с другим номером телефона в нашей системе ({account.phone_number}).",
                    )
                # Если у аккаунта нет TG ID, или если TG ID совпадает (маловероятно здесь), привязываем новый
                # Также проверим, не занят ли новый TG ID кем-то еще
                if (
                    account_by_telegram_id and account_by_telegram_id.id != account.id
                ):  # account_by_telegram_id здесь должен быть None
                    raise TelegramIdConflictException(telegram_id=data.telegram_user_id)
                account.telegram_user_id = data.telegram_user_id
                account.telegram_username = data.telegram_username  # Обновляем username
                session.add(account)
        elif account_by_telegram_id:  # Найден только по Telegram ID
            account = account_by_telegram_id
            # Если номер телефона отличается, обновляем его (после проверки, что новый номер не занят)
            if account.phone_number != data.phone_number:
                if (
                    account_by_phone and account_by_phone.id != account.id
                ):  # account_by_phone здесь должен быть None
                    raise PhoneNumberAlreadyLinkedToDifferentTelegramException(
                        phone_number=data.phone_number
                    )
                account.phone_number = data.phone_number  # Обновляем номер телефона
                if data.full_name_from_telegram:  # Обновляем имя, если оно из Telegram
                    account.full_name = data.full_name_from_telegram
                session.add(account)
        else:  # Не найден ни по телефону, ни по Telegram ID - создаем новый
            if (
                not data.telegram_user_id
            ):  # telegram_user_id обязателен для нового аккаунта через бота
                raise CustomerOnboardingException(
                    detail="Telegram ID не предоставлен для создания нового аккаунта."
                )

            logger.info(
                f"Создание нового аккаунта для тел: {data.phone_number}, TG ID: {data.telegram_user_id}"
            )
            account_create_schema = AccountCreateForClientOnboarding(
                phone_number=data.phone_number,
                full_name=data.full_name_from_telegram,
                is_active=True,
                telegram_user_id=data.telegram_user_id,
                telegram_username=data.telegram_username,
            )
            try:
                account = await self.dao.account.create(
                    session, obj_in=account_create_schema
                )
            except IntegrityError as e:
                # logger.error(f"Ошибка IntegrityError при создании аккаунта для тел: {data.phone_number}: {e.orig}")
                raise CustomerOnboardingException(
                    detail=f"Не удалось зарегистрировать аккаунт из-за конфликта данных (возможно, номер или Telegram ID уже используются)."
                )

        # Активация и обновление имени, если нужно
        if not account.is_active:
            account.is_active = True
            session.add(account)
        if data.full_name_from_telegram and (
            not account.full_name or account.full_name != data.full_name_from_telegram
        ):
            account.full_name = data.full_name_from_telegram
            session.add(account)

        return account

    async def onboard_telegram_client(
        self,
        session: AsyncSession,
        onboarding_data: ClientTelegramOnboardingRequest,
        target_company_id: int,  # ID компании, для которой происходит онбординг
    ) -> CustomerRole:

        # Проверяем, существует ли компания
        company = await self.dao.company.get_active(session, id_=target_company_id)
        if not company:
            # logger.error(f"Попытка онбординга клиента для несуществующей или неактивной компании ID: {target_company_id}")
            raise CompanyNotFoundForOnboardingException(company_id=target_company_id)

        account = await self._get_or_create_account(session, onboarding_data)

        # Найти или создать CustomerRole для этой пары (Account, Company)
        customer_role = await self.dao.customer_role.get_by_account_id_and_company_id(
            session, account_id=account.id, company_id=target_company_id
        )

        if not customer_role:
            from decimal import (  # Add this import at the top of the file if not already present
                Decimal,
            )

            customer_role_create_schema = CustomerRoleCreateInternal(
                account_id=account.id,
                company_id=target_company_id,
                cashback_balance=Decimal("0.0"),  # Начальный баланс
                birth_date=onboarding_data.birth_date,  # Если передается из onboarding_data
            )

            try:
                customer_role = await self.dao.customer_role.create(
                    session, obj_in=customer_role_create_schema
                )
            except (
                IntegrityError
            ) as e:  # На случай, если uq_customer_role_account_company сработает из-за гонки
                # logger.error(f"IntegrityError при создании CustomerRole для Account {account.id}, Company {target_company_id}: {e.orig}")
                # Попробуем получить еще раз, возможно, он только что был создан
                customer_role = (
                    await self.dao.customer_role.get_by_account_id_and_company_id(
                        session, account_id=account.id, company_id=target_company_id
                    )
                )
                if (
                    not customer_role
                ):  # Если все еще нет, то это другая ошибка IntegrityError
                    raise CustomerOnboardingException(
                        detail=f"Не удалось создать профиль клиента в компании из-за конфликта данных. {e.orig}"
                    )
            except Exception as e:
                # logger.error(f"Не удалось создать CustomerRole для Account ID {account.id} в Company ID {target_company_id}: {e}")
                raise CustomerOnboardingException(
                    detail=f"Не удалось создать профиль клиента в компании: {str(e)}"
                )

        await session.flush()

        # Обновляем объекты из БД для консистентности и загрузки связей
        await session.refresh(account)
        await session.refresh(customer_role)
        if not customer_role.account:
            customer_role.account = (
                account  # Устанавливаем связь, если refresh не подтянул
            )
        if not customer_role.company:
            customer_role.company = (
                company  # Устанавливаем связь, если refresh не подтянул
            )

        return customer_role
