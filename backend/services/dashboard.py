from typing import List

from backend.models.account import Account as AccountModel
from backend.schemas.account import AccountResponse as DashboardAccountInfoResponse
from backend.schemas.dashboard import (
    DashboardCompanyAdminResponse,
    DashboardCompanyEmployeeResponse,
    DashboardResponse,
)


class DashboardService:
    async def get_dashboard_data(
        self, current_account: AccountModel
    ) -> DashboardResponse:

        account_info = DashboardAccountInfoResponse.model_validate(
            current_account
        )  # Создаем объект DashboardAccountInfoResponse из данных current_account, проверяя их на соответствие схеме.
        owned_companies_response: List[DashboardCompanyAdminResponse] = []

        if (
            current_account.user_profile
            and current_account.user_profile.companies_owned
        ):
            for company in current_account.user_profile.companies_owned:

                if not company.is_deleted:
                    owned_companies_response.append(
                        DashboardCompanyAdminResponse.model_validate(company)
                    )
        employee_in_companies_response: List[DashboardCompanyEmployeeResponse] = []

        if (
            current_account.employee_profile
            and current_account.employee_profile.company
        ):
            employee_role = current_account.employee_profile
            company_as_employee = employee_role.company

            if not company_as_employee.is_deleted:
                employee_in_companies_response.append(
                    DashboardCompanyEmployeeResponse(
                        id=company_as_employee.id,
                        name=company_as_employee.name,
                        employee_position=employee_role.position,
                        company_status=company_as_employee.status,
                    )
                )
        can_create_company = True

        return DashboardResponse(
            account_info=account_info,
            owned_companies=owned_companies_response,
            employee_in_companies=employee_in_companies_response,
            can_create_company=can_create_company,
        )
