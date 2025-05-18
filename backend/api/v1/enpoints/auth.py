import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (get_auth_service,
                                       get_current_active_user, get_dao,
                                       get_session)
from backend.dao.holder import HolderDAO
from backend.models.user import User
from backend.schemas.auth import OTPVerifyRequest, PhoneRequest
from backend.schemas.token import Token
from backend.schemas.user import UserBase, UserInDBBase
from backend.services.auth import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token-for-swagger", response_model=Token)
async def login_for_swagger_ui(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
    auth_svc: AuthService = Depends(get_auth_service),
    dao: HolderDAO = Depends(get_dao),
) -> Token:
    phone_number: str = form_data.username
    otp_code: str = form_data.password
    try:
        access_token = await auth_svc.verify_otp_and_login(
            db, dao, phone_number=phone_number, otp_code=otp_code
        )
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in verify_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post(
    "/request-otp", response_model=UserInDBBase, status_code=status.HTTP_200_OK
)
async def request_otp_endpoint(
    phone_data: PhoneRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    try:
        user = await auth_svc.request_otp(db, dao, phone_number=phone_data.phone_number)
        return UserInDBBase.model_validate(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in request_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
async def verify_otp_endpoint(
    otp_data: OTPVerifyRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    try:
        access_token = await auth_svc.verify_otp_and_login(
            db, dao, phone_number=otp_data.phone_number, otp_code=otp_data.otp_code
        )
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in verify_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get("/me", response_model=UserBase)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
