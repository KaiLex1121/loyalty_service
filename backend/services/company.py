import datetime
import logging
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.enums.back_office import (CompanyStatusEnum,
                                       SubscriptionStatusEnum,
                                       UserAccessLevelEnum)
from backend.models.account import Account as AccountModel
from backend.models.cashback import Cashback as CashbackConfigModel
from backend.models.company import Company as CompanyModel
from backend.models.subscription import Subscription as SubscriptionModel
from backend.models.tariff_plan import TariffPlan as TariffPlanModel
from backend.models.user_role import UserRole as UserRoleModel
from backend.schemas.cashback import CashbackConfigCreate
from backend.schemas.company import CompanyCreateRequest
from backend.schemas.subscription import SubscriptionCreate
from backend.schemas.user_role import UserRoleCreate

logger = logging.getLogger(__name__)


class CompanyService:

    async def create_company_flow(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        company_data: CompanyCreateRequest,
        account_id: int,
    ) -> CompanyModel:  # Возвращаем SQLAlchemy модель, эндпоинт преобразует в Pydantic

        # Объекты, которые мы создадим и должны будем добавить в сессию
        new_user_role_obj: Optional[UserRoleModel] = None
        new_company_obj: Optional[CompanyModel] = None
        new_cashback_config_obj: Optional[CashbackConfigModel] = None
        new_subscription_obj: Optional[SubscriptionModel] = None
        async with session.begin():
            # 1. Получение или создание UserRole
            current_account = await dao.account.get_by_id_with_profiles(
                session, id_=account_id
            )
            if (
                not current_account
                or not current_account.is_active
                or current_account.is_deleted
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or inactive account.",
                )

            user_role: Optional[UserRoleModel] = current_account.user_profile

            if not user_role:
                user_role_schema = UserRoleCreate(
                    access_level=UserAccessLevelEnum.COMPANY_OWNER,
                    account_id=account_id,
                )
                new_user_role_obj = await dao.user_role.create(
                    session, obj_in=user_role_schema
                )
                user_role = new_user_role_obj
            if not user_role or not user_role.id:
                raise ValueError("UserRole could not be established for the account.")

            # 3. Создание Company
            new_company_obj = await dao.company.create_company_with_owner(
                session,
                obj_in=company_data,
                owner_user_role_id=user_role.id,
                initial_status=CompanyStatusEnum.PENDING_VERIFICATION,
            )

            # 4. Создание CashbackConfig
            cashback_config_schema = CashbackConfigCreate(
                company_id=new_company_obj.id,
                default_percentage=company_data.initial_cashback_percentage,
            )
            new_cashback_config_obj = await dao.cashback_config.create(
                session, obj_in=cashback_config_schema
            )

            # 5. Поиск триального TariffPlan
            trial_plan = await dao.tariff_plan.get_trial_plan(session)
            if not trial_plan:
                raise HTTPException(
                    status_code=500, detail="Trial tariff plan not configured."
                )

            # 6. Создание Subscription
            today = datetime.date.today()
            trial_end = today + relativedelta(months=3)

            subscription_schema = SubscriptionCreate(
                company_id=new_company_obj.id,
                tariff_plan_id=trial_plan.id,
                status=SubscriptionStatusEnum.TRIALING,
                start_date=today,
                trial_end_date=trial_end,
                next_billing_date=trial_end,
                auto_renew=False,
            )
            new_subscription_obj = await dao.subscription.create(
                session, obj_in=subscription_schema
            )

        # Загружаем компанию со всеми нужными связями для ответа API
        # Это гарантирует, что Pydantic схема CompanyResponse получит все данные
        company_for_response = await dao.company.get_by_id_with_relations(
            session, company_id=new_company_obj.id
        )

        if not company_for_response:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve newly created company details for response.",
            )

        return company_for_response
