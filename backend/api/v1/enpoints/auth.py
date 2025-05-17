from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.db.session import get_db
from backend.schemas.user import UserBase
from backend.schemas.auth import PhoneRequest, OTPVerifyRequest
from backend.schemas.token import Token
from backend.services.auth import AuthService, auth_service
from backend.core.dependencies import get_auth_service, get_current_active_user
from backend.models.user import User
from backend.core.dependencies import get_dao
from backend.dao.holder import HolderDAO

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/request-otp", response_model=UserBase, status_code=status.HTTP_200_OK)
async def request_otp_endpoint(
    phone_data: PhoneRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_svc.request_otp(db, phone_number=phone_data.phone_number)
        return UserBase.model_validate(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in request_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.post("/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
async def verify_otp_endpoint(
    otp_data: OTPVerifyRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        access_token = await auth_svc.verify_otp_and_login(
            db,
            phone_number=otp_data.phone_number,
            otp_code=otp_data.otp_code
        )
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in verify_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/me", response_model=UserBase)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return UserBase.model_validate(current_user)