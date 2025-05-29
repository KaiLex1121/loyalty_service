from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import datetime
from dateutil.relativedelta import relativedelta # Для добавления месяцев

from backend.dao.holder import HolderDAO # Ваш HolderDAO
from backend.models.account import Account as AccountModel
from backend.models.company import Company as CompanyModel
from backend.models.user_role import UserRole as UserRoleModel
from backend.models.cashback import CashbackConfig as CashbackConfigModel
from backend.models.subscription import Subscription as SubscriptionModel
from backend.models.tariff_plan import TariffPlan as TariffPlanModel

from backend.schemas.company import CompanyCreateRequest, CompanyResponse
from backend.schemas.user_role import UserRoleCreate
from backend.schemas.cashback import CashbackConfigCreate
from backend.schemas.subscription import SubscriptionCreate

from backend.enums.back_office import AdminAccessLevelEnum, CompanyStatusEnum, SubscriptionStatusEnum

class CompanyService:

    async def create_company_flow(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        company_data: CompanyCreateRequest,
        current_account: AccountModel
    ) -> CompanyModel:

        async with db.begin(): # Управляем транзакцией здесь
            # 1. Получение или создание UserRole
            user_role = current_account.user_role # Предполагаем, что загружен с Account
            if not user_role:
                user_role_schema = UserRoleCreate(access_level=AdminAccessLevelEnum.COMPANY_OWNER)
                # dao.user_role.create_for_account должен добавлять в сессию, но не коммитить
                user_role = await dao.user_role.create_for_account(
                    db, obj_in=user_role_schema, account_id=current_account.id
                )
            elif user_role.access_level != AdminAccessLevelEnum.FULL_SYSTEM_ADMIN:
                # Проверка: если COMPANY_OWNER, может ли он создать еще одну компанию?
                # (Зависит от бизнес-логики, пока разрешаем)
                # Если у него уже есть компании, и он не суперадмин, возможно, стоит ограничить.
                # existing_companies = await dao.company.get_by_owner_role_id(db, owner_role_id=user_role.id)
                # if existing_companies:
                #     raise HTTPException(status_code=403, detail="Company owner can only manage one company or upgrade plan.")
                pass


            # 2. Валидация initial_cashback_percentage (уже сделана Pydantic)
            if company_data.initial_cashback_percentage <= decimal.Decimal("0"):
                 raise HTTPException(status_code=400, detail="Initial cashback percentage must be greater than 0.")

            # 3. Создание Company
            # Исключаем initial_cashback_percentage из данных для Company, т.к. это для CashbackConfig
            company_create_dict = company_data.model_dump(exclude={"initial_cashback_percentage"})

            new_company_obj = CompanyModel(
                **company_create_dict,
                owner_user_role_id=user_role.id,
                status=CompanyStatusEnum.PENDING_VERIFICATION # или ACTIVE, если не нужна верификация
            )
            db.add(new_company_obj)
            await db.flush() # Чтобы получить new_company_obj.id для связей
            # await db.refresh(new_company_obj) # пока не нужен, если нет server_default для полей Company

            # 4. Создание CashbackConfig
            cashback_config_schema = CashbackConfigCreate(
                company_id=new_company_obj.id, # Используем ID созданной компании
                default_percentage=company_data.initial_cashback_percentage,
                is_active=True
            )
            # dao.cashback_config.create должен добавлять в сессию, но не коммитить
            await dao.cashback_config.create(db, obj_in=cashback_config_schema)

            # 5. Поиск триального TariffPlan
            trial_plan = await dao.tariff_plan.get_trial_plan(db)
            if not trial_plan:
                # Это ошибка конфигурации сервера, триальный тариф должен существовать
                raise HTTPException(status_code=500, detail="Trial tariff plan not configured.")

            # 6. Создание Subscription
            today = datetime.date.today()
            trial_end = today + relativedelta(months=3)

            subscription_schema = SubscriptionCreate(
                company_id=new_company_obj.id,
                tariff_plan_id=trial_plan.id,
                status=SubscriptionStatusEnum.TRIALING,
                start_date=today,
                trial_end_date=trial_end,
                next_billing_date=trial_end, # Или trial_end + 1 day, в зависимости от логики биллинга
                auto_renew=True # Обычно триалы пытаются конвертировать в платные
            )
            # dao.subscription.create должен добавлять в сессию, но не коммитить
            await dao.subscription.create(db, obj_in=subscription_schema)

            # Коммит произойдет автоматически при выходе из `async with db.begin():`
            # Обновляем объекты, чтобы получить все данные из БД (включая связи, если они настроены на eager load при refresh)
            await db.refresh(new_company_obj)
            if user_role not in db: # Если user_role был новым
                await db.refresh(user_role)
            # Можно также обновить current_account, если его user_role был создан/изменен
            # await db.refresh(current_account, attribute_names=['user_role'])

        # После коммита и выхода из транзакции, new_company_obj будет содержать актуальные данные
        # Для ответа API может потребоваться загрузить связи, если они не загружены по умолчанию
        # или если refresh их не подтянул так, как нужно для CompanyResponse.
        # Это можно сделать отдельным запросом или настроить eager loading в модели/запросе.
        # Для простоты пока возвращаем то, что есть.
        return new_company_obj

company_service = CompanyService()
