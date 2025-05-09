from fastapi import APIRouter

from app.doctors.router import doctors_router


root_router = APIRouter()

root_router.include_router(doctors_router, prefix="/doctors")
