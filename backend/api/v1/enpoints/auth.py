import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_auth_service, get_dao, get_session
from backend.dao.holder import HolderDAO
from backend.enums.back_office import OtpPurposeEnum
from backend.schemas.account import AccountInDBBase
from backend.schemas.auth import OTPVerifyRequest, PhoneNumberRequest
from backend.schemas.token import Token
from backend.services.auth import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token-for-swagger", response_model=Token)
async def login_for_swagger_ui(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
    dao: HolderDAO = Depends(get_dao),
) -> Token:
    phone_number: str = form_data.username
    otp_code: str = form_data.password

    try:
        otp_request = OTPVerifyRequest(
            otp_code=otp_code,
            purpose=OtpPurposeEnum.BACKOFFICE_LOGIN,
            phone_number=phone_number,
        )
        access_token = await auth_service.verify_otp_and_login(
            session, dao, otp_data=otp_request
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
    "/request-otp", response_model=AccountInDBBase, status_code=status.HTTP_200_OK
)
async def request_otp_endpoint(
    phone_data: PhoneNumberRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    try:
        account = await auth_service.request_otp_for_login(
            session, dao, phone_number=phone_data.phone_number
        )
        return AccountInDBBase.model_validate(account)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in request_otp_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred.",
        )


@router.post("/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
async def verify_otp_endpoint(
    otp_data: OTPVerifyRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    try:
        access_token = await auth_svc.verify_otp_and_login(
            session, dao, otp_data=otp_data
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
