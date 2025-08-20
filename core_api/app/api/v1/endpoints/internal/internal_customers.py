from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_client_onboarding_service, get_client_onboarding_service, get_dao, get_session, verify_internal_api_key
from app.dao.holder import HolderDAO
from app.exceptions.common import NotFoundException
from app.schemas.customer_role import CustomerRoleResponse
from app.schemas.customer_bot_auth import ClientTelegramOnboardingRequest
from app.services.customer_bot_auth import CustomerAuthService


router = APIRouter(dependencies=[Depends(verify_internal_api_key)])



@router.get(
    "/by-telegram-id/{telegram_id}",
    response_model=CustomerRoleResponse,
    summary="Find customer by Telegram ID for a specific company"
)
async def get_customer_by_telegram_id(
    telegram_id: int,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    customer_role = await dao.customer_role.find_by_telegram_id_and_company_id(
        session, telegram_id=telegram_id, company_id=company_id
    )
    if not customer_role:
        raise NotFoundException(
            f"Customer with Telegram ID {telegram_id} not found in company {company_id}"
        )
    return customer_role

@router.post(
    "/onboard",
    response_model=CustomerRoleResponse,
    summary="Onboard a new customer via Bot Gateway"
)
async def onboard_customer(
    onboarding_data: ClientTelegramOnboardingRequest,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: CustomerAuthService = Depends(get_client_onboarding_service),
):
    customer_role = await service.onboard_telegram_client(
        session, onboarding_data, target_company_id=company_id
    )
    return customer_role