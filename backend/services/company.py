import datetime
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logger import get_logger
from backend.dao.holder import HolderDAO
from backend.enums.back_office import (
    CompanyStatusEnum,
    SubscriptionStatusEnum,
    UserAccessLevelEnum,
)
from backend.exceptions import (
    AccountNotFoundException,
    CompanyFlowException,
    CompanyNotFoundException,
    ForbiddenException,
    InternalServerError,
    TrialPlanNotConfiguredException,
)
from backend.models.company import Company as CompanyModel
from backend.models.user_role import UserRole as UserRoleModel
from backend.schemas.cashback import CashbackConfigCreate
from backend.schemas.company import CompanyCreateRequest, CompanyResponse
from backend.schemas.subscription import SubscriptionCreate
from backend.schemas.user_role import UserRoleCreate

logger = get_logger(__name__)


class CompanyService:
    async def create_company_flow(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        company_data: CompanyCreateRequest,
        account_id: int,
    ) -> CompanyResponse:
        async with session.begin():
            current_account = await dao.account.get_by_id_with_profiles(
                session, id_=account_id
            )
            if (
                not current_account
                or not current_account.is_active
                or current_account.is_deleted
            ):
                # Если аккаунт не найден, это AccountNotFoundException.
                # Если найден, но неактивен/удален - это ForbiddenException.
                if not current_account:
                    raise AccountNotFoundException(
                        identifier=account_id, identifier_type="ID"
                    )
                raise ForbiddenException(
                    detail="Account is inactive or deleted, cannot create company.",
                    internal_details={"account_id": account_id, "status_issue": True},
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
                # Это серьезная внутренняя проблема, если UserRole не удалось создать/получить
                raise CompanyFlowException(
                    reason="UserRole could not be established for the account.",
                    internal_details={"account_id": account_id},
                )

            new_company_obj = await dao.company.create_company_with_owner(
                session,
                obj_in=company_data,
                owner_user_role_id=user_role.id,
                initial_status=CompanyStatusEnum.PENDING_VERIFICATION,
            )

            cashback_config_schema = CashbackConfigCreate(
                company_id=new_company_obj.id,
                default_percentage=company_data.initial_cashback_percentage,
            )
            await dao.cashback_config.create(session, obj_in=cashback_config_schema)

            trial_plan = await dao.tariff_plan.get_trial_plan(session)
            if not trial_plan:
                raise TrialPlanNotConfiguredException(
                    internal_details={"context": "Company creation flow"}
                )

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
            await dao.subscription.create(session, obj_in=subscription_schema)

        company_for_response = await dao.company.get_by_id_with_relations(
            session, company_id=new_company_obj.id
        )
        if not company_for_response:
            # Это тоже внутренняя проблема, если только что созданная компания не найдена
            raise CompanyNotFoundException(
                identifier=new_company_obj.id,
                detail="Failed to retrieve newly created company details for response.",
                internal_details={"context": "Post-company creation retrieval"},
            )

        try:
            return CompanyResponse.model_validate(company_for_response)
        except ValidationError as e:
            logger.error(
                f"Failed to validate company {company_for_response.id} for response: {e}",
                exc_info=True,
            )
            raise InternalServerError(
                detail="Internal data validation error when preparing company response.",
                internal_details={
                    "company_id": company_for_response.id,
                    "validation_errors": e.errors(),
                },
            )

    async def get_owned_companies(
        self, user_role: UserRoleModel
    ) -> List[CompanyResponse]:
        # Валидация здесь происходит при создании CompanyResponse.
        # Если данные из БД не проходят валидацию в схему ответа, это внутренняя ошибка.
        # Обработчик ValidationError позаботится об этом, если он не обернут.
        # Либо можно обернуть здесь в InternalServerError.
        companies_validated = []
        for company in user_role.companies_owned:
            if not company.is_deleted:
                try:
                    companies_validated.append(CompanyResponse.model_validate(company))
                except ValidationError as e:
                    logger.error(
                        f"Failed to validate company {company.id} in get_owned_companies: {e}",
                        exc_info=True,
                    )
                    raise InternalServerError(
                        detail=f"Data for company {company.id} is invalid.",
                        internal_details={
                            "company_id": company.id,
                            "errors": e.errors(),
                        },
                    )
        return companies_validated

    async def get_owned_company(self, company: CompanyModel) -> CompanyResponse:
        try:
            return CompanyResponse.model_validate(company)
        except ValidationError as e:
            logger.error(
                f"Failed to validate company {company.id} in get_owned_company: {e}",
                exc_info=True,
            )
            raise InternalServerError(
                detail="Internal data validation error.",
                internal_details={
                    "company_id": company.id,
                    "validation_errors": e.errors(),
                },
            )
