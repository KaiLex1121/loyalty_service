from fastapi import APIRouter

from backend.web_app.routes import auth

web_app_router = APIRouter()
web_app_router.include_router(auth.router, include_in_schema=False)
