from fastapi import APIRouter

from app.api.v1.endpoints.external import (
    backoffice_auth,
    backoffice_dashboards,
    companies,
    company_default_cashback_config,
    company_employees,
    company_outlets,
    company_promotions,
    company_telegram_bots,
    customer_bot_auth,
    customers,
    employee_bot_auth,
    employee_bot_operations,
    company_broadcasts
)
from app.api.v1.endpoints.admin import company_tariff_plans

from app.api.v1.endpoints.internal import internal_customers, internal_telegram_bots

api_router_v1 = APIRouter()

api_router_v1.include_router(
    backoffice_auth.router, prefix="/auth", tags=["Backoffice Authentication"]
)
api_router_v1.include_router(
    backoffice_dashboards.router, prefix="/me", tags=["Backoffice Dashboard"]
)
api_router_v1.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router_v1.include_router(
    company_tariff_plans.router,
    prefix="/admin/tariff-plans",
    tags=["Admin. Company Tariff Plans"],
)
api_router_v1.include_router(
    company_outlets.router, prefix="/companies", tags=["Company Outlets"]
)
api_router_v1.include_router(
    company_employees.router, prefix="/companies", tags=["Company Employees"]
)
api_router_v1.include_router(
    company_default_cashback_config.router,
    prefix="/companies",
    tags=["Company Default Cashback"],
)
api_router_v1.include_router(
    company_promotions.router,
    prefix="/companies/{company_id}/promotions",
    tags=["Company Promotions"],
)
api_router_v1.include_router(
    customer_bot_auth.router,
    prefix="/customer/auth",  # Префикс для эндпоинтов аутентификации клиента
    tags=["Customer - Authentication"],
)
api_router_v1.include_router(
    internal_customers.router,
    prefix="/customers",  # Общий префикс для клиентских данных (пути внутри /me/...)
    tags=["Customers - Profile"],
)
api_router_v1.include_router(
    employee_bot_auth.router,
    prefix="/employee-bot/auth",  # Префикс для эндпоинтов аутентификации сотрудника через бот
    tags=["Employees - Authentication"],
)
api_router_v1.include_router(
    employee_bot_operations.router,
    prefix="/employee-bot/operations",  # Префикс для операций сотрудника после входа
    tags=["Employees - Operations"],
)

api_router_v1.include_router(
    company_telegram_bots.router,
    prefix="/companies/{company_id}/bots",
    tags=["Company Telegram Bots"],
)
api_router_v1.include_router(
    company_broadcasts.router,
    prefix="/companies/{company_id}/broadcasts",
    tags=["Company Broadcasts"],
)

api_router_v1.include_router(internal_telegram_bots.router, prefix="/internal/telegram-bots", tags=["Internal Telegram Bots"])

api_router_v1.include_router(internal_customers.router, prefix="/internal/customers", tags=["Internal Customers"])
