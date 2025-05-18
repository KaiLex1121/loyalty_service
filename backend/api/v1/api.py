from fastapi import APIRouter

from backend.api.v1.enpoints import auth

api_router_v1 = APIRouter()
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
