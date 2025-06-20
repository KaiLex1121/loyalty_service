# backend/services/cashback_service.py
import decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.exceptions.common import (  # Добавил ConflictException
    ConflictException,
    NotFoundException,
    ValidationException,
)
from backend.models.company import Company as CompanyModel
from backend.schemas.cashback import CashbackConfigResponse, CashbackConfigUpdate


class CashbackService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def get_cashback_config(
        self, session: AsyncSession, company: CompanyModel
    ) -> CashbackConfigResponse:
        """
        Получает конфигурацию кэшбэка для компании.
        Предполагается, что company.cashback_config уже загружен зависимостью.
        """
        if not company.cashback_config or company.cashback_config.is_deleted:
            raise NotFoundException(
                resource_name="Cashback Configuration", identifier=company.id
            )

        return CashbackConfigResponse.model_validate(company.cashback_config)

    async def update_cashback_config(
        self,
        session: AsyncSession,
        company: CompanyModel,
        update_data: CashbackConfigUpdate,
    ) -> CashbackConfigResponse:
        """
        Обновляет конфигурацию кэшбэка для компании.
        Предполагается, что company.cashback_config уже загружен зависимостью.
        """
        cashback_config_to_update = company.cashback_config
        if not cashback_config_to_update or cashback_config_to_update.is_deleted:
            raise NotFoundException(
                resource_name="Cashback Configuration", identifier=company.id
            )

        update_dict = update_data.model_dump(exclude_unset=True)

        updated_config_model = await self.dao.cashback_config.update(
            session, db_obj=cashback_config_to_update, obj_in=update_dict
        )

        return CashbackConfigResponse.model_validate(updated_config_model)
