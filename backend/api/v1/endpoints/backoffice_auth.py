from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_auth_service, get_dao, get_session
from backend.core.logger import get_logger
from backend.dao.holder import HolderDAO
from backend.enums.auth_enums import OtpPurposeEnum
from backend.schemas.account import AccountResponse
from backend.schemas.backoffice_auth import OTPVerifyRequest, PhoneNumberRequest
from backend.schemas.token import TokenResponse
from backend.services.backoffice_auth import AuthService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/token-for-swagger", response_model=TokenResponse)
async def login_for_swagger_ui(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
    dao: HolderDAO = Depends(get_dao),
) -> TokenResponse:

    phone_number: str = form_data.username
    otp_code: str = form_data.password

    otp_request = OTPVerifyRequest(
        otp_code=otp_code,
        purpose=OtpPurposeEnum.BACKOFFICE_LOGIN,
        phone_number=phone_number,
    )
    access_token = await auth_service.verify_otp_and_login(
        session, dao, otp_data=otp_request
    )
    return access_token


@router.post(
    "/request-otp", response_model=AccountResponse, status_code=status.HTTP_200_OK
)
async def request_otp_endpoint(
    phone_data: PhoneNumberRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):

    account = await auth_service.request_otp_for_login(
        session, dao, phone_number=phone_data.phone_number
    )
    return account


@router.post(
    "/verify-otp", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def verify_otp_endpoint(
    otp_data: OTPVerifyRequest,
    auth_svc: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):

    access_token = await auth_svc.verify_otp_and_login(session, dao, otp_data=otp_data)
    return access_token
