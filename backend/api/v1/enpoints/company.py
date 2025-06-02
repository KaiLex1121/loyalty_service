import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (get_account_id_from_token,
                                       get_company_service, get_dao,
                                       get_session)
from backend.dao.holder import HolderDAO
from backend.schemas.company import CompanyCreateRequest, CompanyResponse
from backend.services.company import CompanyService

router = APIRouter()
logger = logging.getLogger(__name__)


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
    try:
        new_company = await company_service.create_company_flow(
            session=session,
            dao=dao,
            company_data=company_data,
            account_id=account_id,
        )
        return CompanyResponse.model_validate(new_company)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in create_company_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred.",
        )
