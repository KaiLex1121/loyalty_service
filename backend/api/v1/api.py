from fastapi import APIRouter

from backend.api.v1.enpoints import auth, dashboard, company

api_router_v1 = APIRouter()
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(dashboard.router, prefix="/me", tags=["Dashboard"])
api_router_v1.include_router(company.router, prefix="/company", tags=["Company"])