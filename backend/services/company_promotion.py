# backend/services/promotion.py
import datetime
from typing import Optional, Sequence  # Добавил Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.enums import CashbackTypeEnum, PromotionStatusEnum, PromotionTypeEnum
from backend.enums.loyalty_enums import PromotionPriorityLevelEnum
from backend.exceptions.services.promotion import (
    InvalidPromotionDataException,
    PromotionCreationException,
    PromotionNotFoundException,
    PromotionUpdateException,
)
from backend.models.company import Company
from backend.models.promotions.promotion import Promotion
from backend.schemas.promotion_cashback_config import (
    CashbackConfigUpdate,  # Нужна для promo_update_data.cashback_config
)
from backend.schemas.promotion_cashback_config import (
    CashbackConfigCreateInternal,
)
from backend.schemas.company_promotion import (
    INT_TO_PRIORITY_LEVEL_MAP,
    PRIORITY_LEVEL_TO_INT_MAP,
    PromotionCreate,
    PromotionCreateInternal,
    PromotionUpdate,
)

# from backend.core.logger import get_logger # Раскомментируйте, если используете
# logger = get_logger(__name__)


class PromotionService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def _validate_promotion_name_for_company(
        self,
        session: AsyncSession,
        name: str,
        company_id: int,
        existing_promotion_id: Optional[int] = None,
    ) -> None:
        """Проверяет, что имя акции уникально для компании, исключая саму себя при обновлении."""
        promo_with_same_name = await self.dao.promotion.find_by_name_for_company(
            session, name=name, company_id=company_id
        )
        if promo_with_same_name and (
            existing_promotion_id is None
            or promo_with_same_name.id != existing_promotion_id
        ):
            raise PromotionCreationException(  # Используем это исключение и для создания, и для обновления при конфликте имени
                detail=f"Акция с названием '{name}' уже существует для данной компании."
            )

    async def _validate_promotion_dates(
        self, start_date: datetime.datetime, end_date: Optional[datetime.datetime]
    ) -> None:
        """Проверяет корректность дат акции."""
        if end_date and end_date < start_date:
            raise InvalidPromotionDataException(
                "Дата окончания акции не может быть раньше даты начала."
            )

    async def create_promotion(
        self,
        session: AsyncSession,
        company: Company,
        promo_data: PromotionCreate,  # Принимает priority_level: PromotionPriorityLevelEnum
    ) -> Promotion:
        await self._validate_promotion_name_for_company(
            session, promo_data.name, company.id
        )
        await self._validate_promotion_dates(promo_data.start_date, promo_data.end_date)

        if promo_data.promotion_type != PromotionTypeEnum.CASHBACK:  # Проверка для MVP
            raise InvalidPromotionDataException(
                f"В текущей версии поддерживается только тип акции '{PromotionTypeEnum.CASHBACK.value}'."
            )

        if not promo_data.cashback_config:  # Обязателен для типа CASHBACK
            raise InvalidPromotionDataException(
                "Конфигурация кэшбэка обязательна для акций типа 'CASHBACK'."
            )

        # Преобразование уровня приоритета в число
        DEFAULT_NUMERIC_PRIORITY = DEFAULT_NUMERIC_PRIORITY = PRIORITY_LEVEL_TO_INT_MAP[
            PromotionPriorityLevelEnum.MEDIUM
        ]

        numeric_priority = PRIORITY_LEVEL_TO_INT_MAP.get(
            promo_data.priority_level, DEFAULT_NUMERIC_PRIORITY
        )

        # Формируем Internal схему для DAO
        promo_internal_data = PromotionCreateInternal(
            **(promo_data.model_dump(exclude={"cashback_config", "priority_level"})),
            company_id=company.id,
            current_total_uses=0,
            priority=numeric_priority,  # Передаем числовой приоритет
        )

        try:
            new_promotion = await self.dao.promotion.create(
                session, obj_in=promo_internal_data
            )

            # Создание CashbackConfig
            cashback_config_internal_data = CashbackConfigCreateInternal(
                **(promo_data.cashback_config.model_dump()),
                promotion_id=new_promotion.id,
            )
            await self.dao.cashback_config.create(
                session, obj_in=cashback_config_internal_data
            )

            await session.flush()
            await session.refresh(new_promotion, attribute_names=["cashback_config"])

            # logger.info(f"Акция {new_promotion.id} ('{new_promotion.name}') создана для компании {company.id} с приоритетом {numeric_priority}.")
            return new_promotion
        except IntegrityError as e:
            # logger.error(f"Ошибка целостности БД при создании акции для компании {company.id}: {e.orig}")
            # Повторная проверка имени, если IntegrityError был из-за uq_promotion_company_name
            await self._validate_promotion_name_for_company(
                session, promo_data.name, company.id
            )
            raise PromotionCreationException(
                detail=f"Ошибка базы данных: не удалось создать акцию. {e.orig}"
            )
        except Exception as e:
            # logger.error(f"Непредвиденная ошибка при создании акции для компании {company.id}: {e}")
            raise PromotionCreationException(
                detail=f"Произошла непредвиденная ошибка при создании акции: {str(e)}"
            )

    async def get_promotion_details(
        self,
        session: AsyncSession,
        promotion: Promotion,  # Принимает уже проверенную и загруженную акцию
    ) -> Promotion:
        # Зависимость get_owned_promotion уже должна была загрузить promotion с cashback_config.
        # Если нужна 100% гарантия свежести или загрузки конкретных связей, можно добавить refresh.
        # await session.refresh(promotion, attribute_names=['cashback_config']) # Пример
        return promotion

    async def update_promotion(
        self,
        session: AsyncSession,
        promotion_to_update: Promotion,  # Уже загруженный и проверенный объект
        promo_update_data: PromotionUpdate,  # Принимает optional priority_level
    ) -> Promotion:

        update_payload_for_promo_model = promo_update_data.model_dump(
            exclude_unset=True,
            exclude={
                "cashback_config",
                "priority_level",
            },  # Исключаем поля, обрабатываемые отдельно
        )

        # Обработка имени и дат
        if (
            "name" in update_payload_for_promo_model
            and update_payload_for_promo_model["name"] != promotion_to_update.name
        ):
            await self._validate_promotion_name_for_company(
                session,
                name=update_payload_for_promo_model["name"],
                company_id=promotion_to_update.company_id,
                existing_promotion_id=promotion_to_update.id,
            )

        prospective_start_date = update_payload_for_promo_model.get(
            "start_date", promotion_to_update.start_date
        )
        # Используем model_fields_set (Pydantic V2) для проверки, было ли поле end_date явно передано
        prospective_end_date = (
            promo_update_data.end_date
            if "end_date" in promo_update_data.model_fields_set
            else promotion_to_update.end_date
        )
        await self._validate_promotion_dates(
            prospective_start_date, prospective_end_date
        )

        # Обновление числового приоритета, если передан priority_level
        if (
            promo_update_data.priority_level is not None
        ):  # Проверяем, было ли поле передано
            numeric_priority = PRIORITY_LEVEL_TO_INT_MAP.get(
                promo_update_data.priority_level,
                promotion_to_update.priority,  # Оставляем текущий, если передан неверный уровень (или DEFAULT_NUMERIC_PRIORITY)
            )
            update_payload_for_promo_model["priority"] = numeric_priority

        try:
            updated_promotion = promotion_to_update  # Начинаем с текущего объекта
            if (
                update_payload_for_promo_model
            ):  # Если есть что обновлять в основной модели (включая priority)
                updated_promotion = await self.dao.promotion.update(
                    session,
                    db_obj=promotion_to_update,
                    obj_in=update_payload_for_promo_model,
                )

            config_was_actually_updated = False
            if (
                promo_update_data.cashback_config is not None
            ):  # Если объект cashback_config передан для обновления
                if updated_promotion.promotion_type != PromotionTypeEnum.CASHBACK:
                    # Если пытаются обновить конфиг для не-кэшбэк акции и переданы данные
                    if promo_update_data.cashback_config.model_dump(exclude_unset=True):
                        raise InvalidPromotionDataException(
                            "Нельзя обновить cashback_config для акции, не являющейся кэшбэк-акцией."
                        )
                else:
                    current_cashback_config = updated_promotion.cashback_config
                    if not current_cashback_config:
                        raise InvalidPromotionDataException(
                            f"Отсутствует CashbackConfig для акции {updated_promotion.id}, обновление невозможно."
                        )

                    cashback_update_payload = (
                        promo_update_data.cashback_config.model_dump(exclude_unset=True)
                    )
                    if cashback_update_payload:  # Если есть что обновлять в конфиге
                        # Валидация типа кэшбэка и полей
                        prospective_cb_type = cashback_update_payload.get(
                            "cashback_type", current_cashback_config.cashback_type
                        )

                        prospective_cb_percentage = cashback_update_payload.get(
                            "cashback_percentage"
                        )
                        if (
                            "cashback_percentage" not in cashback_update_payload
                        ):  # Pydantic V2: model_fields_set
                            prospective_cb_percentage = (
                                current_cashback_config.cashback_percentage
                            )

                        prospective_cb_amount = cashback_update_payload.get(
                            "cashback_amount"
                        )
                        if "cashback_amount" not in cashback_update_payload:
                            prospective_cb_amount = (
                                current_cashback_config.cashback_amount
                            )

                        if (
                            prospective_cb_type == CashbackTypeEnum.PERCENTAGE
                            and prospective_cb_percentage is None
                        ):
                            raise InvalidPromotionDataException(
                                "Поле 'cashback_percentage' обязательно, если тип кэшбэка 'PERCENTAGE'."
                            )
                        if (
                            prospective_cb_type == CashbackTypeEnum.FIXED_AMOUNT
                            and prospective_cb_amount is None
                        ):
                            raise InvalidPromotionDataException(
                                "Поле 'cashback_amount' обязательно, если тип кэшбэка 'FIXED_AMOUNT'."
                            )

                        if (
                            "cashback_type" in cashback_update_payload
                        ):  # Если тип явно меняется
                            if prospective_cb_type == CashbackTypeEnum.PERCENTAGE:
                                cashback_update_payload["cashback_amount"] = None
                            elif prospective_cb_type == CashbackTypeEnum.FIXED_AMOUNT:
                                cashback_update_payload["cashback_percentage"] = None

                        await self.dao.cashback_config.update(
                            session,
                            db_obj=current_cashback_config,
                            obj_in=cashback_update_payload,
                        )
                        config_was_actually_updated = True

            if update_payload_for_promo_model or config_was_actually_updated:
                await session.flush()
                await session.refresh(
                    updated_promotion, attribute_names=["cashback_config"]
                )
                # logger.info(f"Акция {updated_promotion.id} обновлена для компании {updated_promotion.company_id}.")

            return updated_promotion
        except IntegrityError as e:
            # logger.error(f"Ошибка целостности БД при обновлении акции {promotion_to_update.id}: {e.orig}")
            if (
                "name" in update_payload_for_promo_model
            ):  # Если ошибка могла быть из-за имени
                await self._validate_promotion_name_for_company(
                    session,
                    name=update_payload_for_promo_model["name"],
                    company_id=promotion_to_update.company_id,
                    existing_promotion_id=promotion_to_update.id,
                )
            raise PromotionUpdateException(
                detail=f"Ошибка базы данных: не удалось обновить акцию. {e.orig}"
            )
        except Exception as e:
            # logger.error(f"Непредвиденная ошибка при обновлении акции {promotion_to_update.id}: {e}")
            raise PromotionUpdateException(
                detail=f"Произошла непредвиденная ошибка при обновлении акции: {str(e)}"
            )

    async def get_promotions_for_company(
        self, session: AsyncSession, company_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Promotion]:
        # logger.debug(f"Получение акций для компании {company_id}, пропустить={skip}, лимит={limit}")
        return await self.dao.promotion.get_promotions_by_company_id(
            session, company_id, skip, limit
        )

    async def delete_promotion(
        self, session: AsyncSession, promotion_to_delete: Promotion
    ) -> Promotion:
        # logger.info(f"Попытка мягкого удаления акции {promotion_to_delete.id} ('{promotion_to_delete.name}')")
        deleted_promo = await self.dao.promotion.soft_delete(
            session, id_=promotion_to_delete.id
        )
        if not deleted_promo:
            # logger.error(f"Не удалось мягко удалить акцию {promotion_to_delete.id} - не найдена DAO или уже удалена.")
            raise PromotionNotFoundException(identifier=promotion_to_delete.id)

        # logger.info(f"Акция {deleted_promo.id} ('{deleted_promo.name}') мягко удалена.")
        return deleted_promo
