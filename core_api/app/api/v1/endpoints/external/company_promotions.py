# backend/api/v1/endpoints/company_promotions.py
from typing import List

from app.core.dependencies import (
    get_owned_company,
    get_owned_promotion,
    get_promotion_service,
    get_session,
)
from app.models.company import Company as CompanyModel
from app.models.promotions.promotion import Promotion as PromotionModel
from app.schemas.company_promotion import (
    PromotionCreate,
    PromotionListItemResponse,
    PromotionResponse,
    PromotionUpdate,
)
from app.services.company_promotion import PromotionService
from fastapi import (  # Убрал HTTPException, т.к. есть хендлеры
    APIRouter,
    Depends,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

# Кастомные исключения больше не нужно импортировать здесь для отлова

router = APIRouter()


@router.post(
    "",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую акцию для компании",
    description="Создает новую акцию лояльности для указанной компании.",
)
async def create_company_promotion_endpoint(
    promo_data: PromotionCreate,
    company: CompanyModel = Depends(get_owned_company),
    service: PromotionService = Depends(get_promotion_service),
    session: AsyncSession = Depends(get_session),
):
    # Просто вызываем сервис. Если он выбросит PromotionCreationException или InvalidPromotionDataException,
    # base_app_exception_handler его поймает и вернет корректный HTTP ответ.
    created_promotion = await service.create_promotion(session, company, promo_data)
    return created_promotion


@router.get(
    "",
    response_model=List[PromotionListItemResponse],
    summary="Получить список акций для компании",
    description="Возвращает список акций (с основной информацией) для указанной компании.",
)
async def get_company_promotions_list_endpoint(
    company: CompanyModel = Depends(get_owned_company),
    skip: int = 0,
    limit: int = 100,
    service: PromotionService = Depends(get_promotion_service),
    session: AsyncSession = Depends(get_session),
):
    promotions = await service.get_promotions_for_company(
        session, company.id, skip, limit
    )
    return promotions


@router.get(
    "/{promotion_id}",
    response_model=PromotionResponse,
    summary="Получить информацию о конкретной акции компании",
    description="Возвращает детальную информацию об указанной акции, если она принадлежит компании.",
)
async def get_company_promotion_details_endpoint(
    promotion: PromotionModel = Depends(get_owned_promotion),
):
    return promotion


@router.put(
    "/{promotion_id}",
    response_model=PromotionResponse,
    summary="Обновить информацию об акции компании",
    description="Обновляет данные указанной акции компании.",
)
async def update_company_promotion_endpoint(
    update_data: PromotionUpdate,
    promotion_to_update: PromotionModel = Depends(get_owned_promotion),
    service: PromotionService = Depends(get_promotion_service),
    session: AsyncSession = Depends(get_session),
):
    updated_promotion = await service.update_promotion(
        session, promotion_to_update, update_data
    )
    return updated_promotion


@router.delete(
    "/{promotion_id}",
    response_model=PromotionResponse,
    summary="Архивировать (мягко удалить) акцию компании",
    description="Устанавливает флаг 'deleted_at' для указанной акции компании.",
)
async def archive_company_promotion_endpoint(
    promotion_to_archive: PromotionModel = Depends(get_owned_promotion),
    service: PromotionService = Depends(get_promotion_service),
    session: AsyncSession = Depends(get_session),
):
    archived_promotion = await service.delete_promotion(session, promotion_to_archive)
    return archived_promotion
