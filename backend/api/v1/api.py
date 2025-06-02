from fastapi import APIRouter

from backend.api.v1.enpoints import admin_tariff_plan, auth, company, dashboard

api_router_v1 = APIRouter()
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(dashboard.router, prefix="/me", tags=["Dashboard"])
api_router_v1.include_router(company.router, prefix="/company", tags=["Company"])
api_router_v1.include_router(
    admin_tariff_plan.router,
    prefix="/admin/tariff-plans",
    tags=["Admin - Tariff Plans"],
)  # <--- Подключаем
