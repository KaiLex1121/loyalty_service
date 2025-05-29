# backend/api/v1/endpoints/companies.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import deps
from backend.core.dependencies import get_company_service, get_dao, get_session
from backend.models.account import Account as AccountModel
from backend.schemas.company import CompanyCreateRequest, CompanyResponse
from backend.dao.holder import HolderDAO
from backend.services.company import CompanyService # Для передачи в сервис

router = APIRouter()

@router.post(
    "", # Путь будет /api/v1/companies
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую компанию"
)
async def create_company_endpoint(
    company_data: CompanyCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_account: AccountModel = Depends(deps.get_current_active_account),
    dao: HolderDAO = Depends(get_dao),
    company_service: CompanyService= Depends(get_company_service),
):
    try:
        new_company = await company_service.create_company_flow(
            session=session, dao=dao, company_data=company_data, current_account=current_account
        )
        return CompanyResponse.model_validate(new_company)
    except HTTPException:
        raise # Пробрасываем HTTP исключения из сервиса