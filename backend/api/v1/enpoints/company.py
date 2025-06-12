from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_account_id_from_token,
    get_company_service,
    get_current_user_profile_from_account,
    get_dao,
    get_owned_company,
    get_session,
)
from backend.core.logger import get_logger
from backend.dao.holder import HolderDAO
from backend.models.company import Company
from backend.models.user_role import UserRole
from backend.schemas.company import CompanyCreateRequest, CompanyResponse
from backend.services.company import CompanyService

router = APIRouter()

logger = get_logger(__name__)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую компанию",
)
async def create_company_endpoint(
    company_data: CompanyCreateRequest,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    account_id: int = Depends(get_account_id_from_token),
    company_service: CompanyService = Depends(get_company_service),
):
    new_company = await company_service.create_company_flow(
        session=session,
        dao=dao,
        company_data=company_data,
        account_id=account_id,
    )
    return new_company


@router.get(
    "",
    response_model=List[CompanyResponse],
    summary="Получить список компаний, которыми владеет пользователь",
)
async def get_owned_companies_endpoint(
    current_user_role: UserRole = Depends(get_current_user_profile_from_account),
    company_service: CompanyService = Depends(get_company_service),
):
    owned_companies = await company_service.get_owned_companies(current_user_role)
    return owned_companies


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Получить информацию о конкретной компании",
)
async def get_company_by_id_endpoint(
    company: Company = Depends(get_owned_company),
    company_service: CompanyService = Depends(get_company_service),
):
    owned_company = await company_service.get_owned_company(company)
    return owned_company
