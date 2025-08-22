from app.core.dependencies import (
    get_client_onboarding_service,
    get_dao,
    get_session,
    verify_internal_api_key,
)
from app.dao.holder import HolderDAO
from app.exceptions.common import NotFoundException
from app.schemas.company_promotion import PromotionResponse
from app.schemas.customer_bot_auth import (
    ClientTelegramOnboardingRequest,
    CustomerProfileResponse,
)
from app.schemas.customer_role import CustomerRoleResponse
from app.schemas.transaction import TransactionResponse
from app.services.customer_bot_auth import CustomerAuthService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


@router.get(
    "/{customer_role_id}/balance",
    response_model=CustomerProfileResponse,  # Возвращаем весь профиль, там есть баланс
    summary="Get customer balance",
)
async def get_customer_balance(
    customer_role_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    customer_role = await dao.customer_role.get(session, id_=customer_role_id)
    if not customer_role:
        raise NotFoundException("Customer profile not found")
    return customer_role


@router.get(
    "/{customer_role_id}/transactions",
    response_model=list[TransactionResponse],
    summary="Get customer transaction history",
)
async def get_transaction_history(
    customer_role_id: int,
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    transactions = await dao.transaction.get_latest_for_customer_by_id(
        session, customer_role_id=customer_role_id, limit=limit
    )
    return transactions


@router.get(
    "/promotions",
    response_model=list[PromotionResponse],
    summary="Get active promotions for a company",
)
async def get_active_promotions(
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
):
    promotions = await dao.promotion.get_active_promotions_for_company_with_details(
        session, company_id=company_id
    )
    # TODO: Добавить сюда и дефолтный кэшбэк компании
    return promotions


@router.get(
    "/by-telegram-id/{telegram_id}",
    response_model=CustomerRoleResponse,
    summary="Find customer by Telegram ID for a specific company",
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
    summary="Onboard a new customer via Bot Gateway",
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
