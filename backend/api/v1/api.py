from fastapi import APIRouter

from backend.api.v1.enpoints import (
    admin_tariff_plans,
    auth,
    companies,
    company_default_cashback_config,
    company_employees,
    company_outlets,
    dashboards,
)

api_router_v1 = APIRouter()

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(dashboards.router, prefix="/me", tags=["Dashboard"])
api_router_v1.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router_v1.include_router(
    admin_tariff_plans.router,
    prefix="/admin/tariff-plans",
    tags=["Admin - Tariff Plans"],
)
api_router_v1.include_router(
    company_outlets.router, prefix="/companies", tags=["Outlets"]
)
api_router_v1.include_router(
    company_employees.router, prefix="/companies", tags=["Employees"]
)
api_router_v1.include_router(
    company_default_cashback_config.router,
    prefix="/companies",
    tags=["Company Default Cashback"],
)
