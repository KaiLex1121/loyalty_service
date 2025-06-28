# from typing import List

# from fastapi import APIRouter, Depends, status
# from sqlalchemy.ext.asyncio import AsyncSession

# from backend.core.dependencies import (
#     get_employee_service,
#     get_owned_company,
#     get_owned_employee_role,
#     get_session,
# )
# from backend.models.company import Company as CompanyModel
# from backend.models.employee_role import EmployeeRole
# from backend.models.outlet import Outlet as OutletModel
# from backend.schemas.company_employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
# from backend.schemas.company_outlet import OutletCreate, OutletResponse, OutletUpdate
# from backend.services.company_employee import EmployeeService
# from backend.services.company_outlet import OutletService

# router = APIRouter()


# @router.get(
#     "/{company_id}/customers/{customer_role_id}",
#     response_model=EmployeeResponse,
#     summary="Get specific company employee",
# )
# async def get_company_employee(
#     employee_role: EmployeeRole = Depends(get_owned_employee_role),
#     session: AsyncSession = Depends(get_session),
#     employee_service: EmployeeService = Depends(get_employee_service),
# ):
#     """Returns detailed information about specific company employee."""
#     return await employee_service.get_customer_response_by_id(session, employee_role)



# @router.get(
#     "/{company_id}/customers",
#     response_model=List[EmployeeResponse],
#     summary="Получить список клиентов компании",
# )
# async def get_company_customers_endpoint(
#     company: CompanyModel = Depends(get_owned_company),  # Проверка доступа к company_id
#     skip: int = 0,
#     limit: int = 100,
#     session: AsyncSession = Depends(get_session),
#     employee_service: EmployeeService = Depends(get_employee_service),
# ):
#     """
#     Возвращает список клиентов для указанной компании, к которой текущий пользователь имеет доступ.
#     """
#     return await employee_service.get_customers_for_company(
#         session, company.id, skip, limit
#     )