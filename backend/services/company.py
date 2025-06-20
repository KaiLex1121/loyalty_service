import datetime
from decimal import Decimal
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logger import get_logger
from backend.core.settings import AppSettings
from backend.dao.holder import HolderDAO
from backend.enums import (
    CompanyStatusEnum,
    SubscriptionStatusEnum,
    UserAccessLevelEnum,
)
from backend.exceptions import (
    AccountNotFoundException,
    BasePlanNotConfiguredException,
    CompanyFlowException,
    CompanyNotFoundException,
    ForbiddenException,
    InternalServerError,
)
from backend.exceptions.services.cashback import CashbackNotConfiguredException
from backend.exceptions.services.company import (
    ActiveSubscriptionsNotFoundException,
    InnConflictException,
    OgrnConflictException,
    SubscriptionsNotFoundException,
)
from backend.models.company import Company as CompanyModel
from backend.models.promotions.cashback_config import CashbackConfig
from backend.models.subscription import Subscription
from backend.models.tariff_plan import TariffPlan
from backend.models.user_role import UserRole as UserRoleModel
from backend.schemas.cashback import CashbackConfigCreate, CashbackConfigResponse
from backend.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from backend.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponseForCompany,
)
from backend.schemas.tariff_plan import TariffPlanResponseForCompany
from backend.schemas.user_role import UserRoleCreate
from backend.utils.subscription_utils import get_current_subscription

logger = get_logger(__name__)


class CompanyService:
    def __init__(self, settings: AppSettings, dao: HolderDAO):
        self.settings = settings
        self.dao = dao

    def _build_company_response(
        self,
        company_model: CompanyModel,
    ) -> CompanyResponse:
        """Собирает CompanyResponse из CompanyModel и ее связей."""

        subscription_model = get_current_subscription(company_model)

        tariff_plan_info = TariffPlanResponseForCompany.model_validate(
            subscription_model.tariff_plan
        )

        if not tariff_plan_info:
            raise BasePlanNotConfiguredException(
                detail="Tariff plan is not configured.",
                internal_details={"context": "CompanyService._build_company_response"},
            )

        current_subscription_response = SubscriptionResponseForCompany(
            id=subscription_model.id,
            status=subscription_model.status,
            next_billing_date=subscription_model.next_billing_date,
            auto_renew=subscription_model.auto_renew,
            tariff_plan=tariff_plan_info,
        )

        cashback_response = CashbackConfigResponse.model_validate(
            company_model.cashback_config
        )

        if not cashback_response:
            raise CashbackNotConfiguredException(
                detail="Cashback is not configured.",
                internal_details={"context": "CompanyService._build_company_response"},
            )

        company_base_data = {
            field: getattr(company_model, field)
            for field in CompanyResponse.model_fields
            if hasattr(company_model, field)
            and field
            not in [
                "owner_user_role",
                "current_subscription",
                "cashback",
                "created_at",
                "updated_at",
                "id",
                "status",
            ]
        }

        return CompanyResponse(
            id=company_model.id,
            status=company_model.status,
            created_at=company_model.created_at,
            updated_at=company_model.updated_at,
            current_subscription=current_subscription_response,
            cashback=cashback_response,
            **company_base_data,
        )

    async def create_company_flow(
        self,
        session: AsyncSession,
        company_data: CompanyCreate,
        account_id: int,
    ) -> CompanyResponse:
        current_account = await self.dao.account.get_by_id_with_profiles(
            session, id_=account_id
        )
        if (
            not current_account
            or not current_account.is_active
            or current_account.is_deleted
        ):
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
            new_user_role_obj = await self.dao.user_role.create(
                session, obj_in=user_role_schema
            )
            user_role = new_user_role_obj

        if not user_role or not user_role.id:
            raise CompanyFlowException(
                reason="UserRole could not be established for the account.",
                internal_details={"account_id": account_id},
            )

        existing_company_by_inn = await self.dao.company.get_by_inn(
            session, inn=company_data.inn
        )
        if existing_company_by_inn:
            raise InnConflictException(inn=company_data.inn)

        if company_data.ogrn:
            existing_company_by_ogrn = await self.dao.company.get_by_ogrn(
                session, ogrn=company_data.ogrn
            )
            if existing_company_by_ogrn:
                raise OgrnConflictException(ogrn=company_data.ogrn)

        new_company_obj = await self.dao.company.create_company_with_owner(
            session,
            obj_in=company_data,
            owner_user_role_id=user_role.id,
            initial_status=CompanyStatusEnum.ACTIVE,
        )

        cashback_config_schema = CashbackConfigCreate(
            company_id=new_company_obj.id,
            default_percentage=company_data.initial_cashback_percentage,
        )
        await self.dao.cashback_config.create(session, obj_in=cashback_config_schema)

        tariff_plan_name = self.settings.TRIAL_PLAN.INTERNAL_NAME
        base_tariff_plan_model = await self.dao.tariff_plan.get_by_internal_name(
            session, internal_name=tariff_plan_name
        )

        if not base_tariff_plan_model:
            raise BasePlanNotConfiguredException(
                internal_details={"context": "CompanyService.create_company_flow"}
            )

        trial_start = datetime.date.today()
        trial_period_days = self.settings.TRIAL_PLAN.DEFAULT_DURATION_DAYS
        trial_end = trial_start + relativedelta(days=trial_period_days)

        subscription_schema = SubscriptionCreate(
            company_id=new_company_obj.id,
            tariff_plan_id=base_tariff_plan_model.id,
            status=SubscriptionStatusEnum.TRIALING,
            start_date=trial_start,
            trial_end_date=trial_end,
            next_billing_date=trial_end,
            auto_renew=True,
            current_price=Decimal("0.00"),
        )
        await self.dao.subscription.create(session, obj_in=subscription_schema)

        company_for_response = await self.dao.company.get_company_detailed_by_id(
            session, company_id=new_company_obj.id
        )
        if not company_for_response:
            raise CompanyNotFoundException(
                identifier=new_company_obj.id,
                detail="Failed to retrieve newly created company details for response.",
                internal_details={"context": "Post-company creation retrieval"},
            )

        try:
            return self._build_company_response(
                company_model=company_for_response,
            )
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

    async def update_company(
        self,
        session: AsyncSession,
        company_to_update: CompanyModel,
        update_data: CompanyUpdate,
    ) -> CompanyResponse:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        if (
            "inn" in update_data_dict
            and update_data_dict["inn"] != company_to_update.inn
        ):
            existing_company = await self.dao.company.get_by_inn(
                session, inn=update_data_dict["inn"]
            )
            if existing_company and existing_company.id != company_to_update.id:
                raise InnConflictException(
                    inn=update_data_dict["inn"],
                    internal_details={"company_id": existing_company.id},
                )

        updated_company = await self.dao.company.update(
            session, db_obj=company_to_update, obj_in=update_data_dict
        )

        company_for_response = await self.dao.company.get_company_detailed_by_id(
            session, company_id=updated_company.id
        )

        if not company_for_response:
            raise CompanyNotFoundException(
                identifier=updated_company.id,
                detail="Failed to retrieve updated company details for response.",
                internal_details={"context": "Post-company update retrieval"},
            )

        return self._build_company_response(company_model=company_for_response)

    async def get_owned_companies(
        self, user_role: UserRoleModel, session: AsyncSession
    ) -> List[CompanyResponse]:

        user_role_with_detailed_companies = (
            await self.dao.user_role.get_user_role_companies_detailed(
                user_role_id=user_role.id, session=session
            )
        )

        if (
            not user_role_with_detailed_companies
            or not user_role_with_detailed_companies.companies_owned
        ):
            return []

        companies_validated = []
        for company in user_role_with_detailed_companies.companies_owned:
            if not company.is_deleted:
                try:
                    companies_validated.append(self._build_company_response(company))
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
            return self._build_company_response(company)
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
