# backend/services/employee_service.py

from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Для явного select, если понадобится
from sqlalchemy.orm import selectinload

from backend.dao.holder import HolderDAO
from backend.enums import SubscriptionStatusEnum
from backend.exceptions.services.employee import (
    ConflictException,
    EmployeeAlreadyExistsInCompanyException,
    EmployeeLimitExceededException,
    EmployeeNotFoundException,
)
from backend.exceptions.services.outlet import InvalidOutletForAssignmentException
from backend.models.account import Account as AccountModel
from backend.models.company import Company as CompanyModel
from backend.models.employee_role import EmployeeRole as EmployeeRoleModel
from backend.models.outlet import (
    Outlet as OutletModel,  # Для проверки и получения объектов Outlet
)
from backend.models.subscription import (
    Subscription as SubscriptionModel,  # Для _get_current_active_subscription
)
from backend.schemas.account import AccountCreate, AccountCreateInternal
from backend.schemas.employee import (
    AccountResponseForEmployee,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    OutletResponseForEmployee,
)
from backend.utils.subscription_utils import get_current_subscription


class EmployeeService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def _build_employee_response(
        self, session: AsyncSession, employee_role: EmployeeRoleModel
    ) -> EmployeeResponse:
        """Собирает EmployeeResponse из EmployeeRoleModel и его связей."""
        # Убедимся, что account и assigned_outlets загружены
        # DAO методы get_by_id_with_details и get_multi_by_company_id_with_details должны это делать.
        if not employee_role.account:
            # Этого не должно происходить, если DAO отработал правильно
            await session.refresh(employee_role, ["account"])
        if (
            not hasattr(employee_role, "assigned_outlets")
            or employee_role.assigned_outlets is None
        ):
            await session.refresh(employee_role, ["assigned_outlets"])

        account_info = AccountResponseForEmployee.model_validate(employee_role.account)
        outlets_info = [
            OutletResponseForEmployee.model_validate(outlet)
            for outlet in employee_role.assigned_outlets
        ]

        return EmployeeResponse(
            id=employee_role.id,
            company_id=employee_role.company_id,
            position=employee_role.position,
            work_full_name=employee_role.work_full_name,
            work_email=employee_role.work_email,
            work_phone_number=employee_role.work_phone_number,
            account=account_info,
            assigned_outlets=outlets_info,
            created_at=employee_role.created_at,
            updated_at=employee_role.updated_at,
            deleted_at=employee_role.deleted_at,
        )

    async def _validate_and_get_outlets_for_assignment(
        self, session: AsyncSession, outlet_ids: List[int], company_id: int
    ) -> List[OutletModel]:
        if not outlet_ids:
            return []
        unique_requested_ids = set(outlet_ids)  # Работаем с уникальными ID

        valid_outlets_found = (
            await self.dao.outlet.get_active_outlets_by_ids_and_company_id(
                session, outlet_ids, company_id
            )
        )
        # Проверяем, все ли запрошенные уникальные ID были найдены среди валидных
        if len(valid_outlets_found) != len(unique_requested_ids):
            # Находим, какие именно ID не были найдены или не прошли валидацию на уровне БД
            found_ids = {o.id for o in valid_outlets_found}
            missing_or_invalid_ids = [
                oid for oid in unique_requested_ids if oid not in found_ids
            ]
            raise InvalidOutletForAssignmentException(
                outlets_id=missing_or_invalid_ids,
                company_id=company_id,
                detail=f"Some outlets from list {missing_or_invalid_ids} are invalid or do not belong to company {company_id}.",
            )

        return valid_outlets_found

    async def add_employee_to_company(
        self,
        session: AsyncSession,
        company: CompanyModel,  # Компания, в которую добавляем (уже проверена на доступ и загружена с подписками)
        employee_data: EmployeeCreate,
    ) -> EmployeeResponse:
        # Транзакция управляется извне

        # 1. Найти или создать Account по employee_data.account_phone_number
        account = await self.dao.account.get_by_phone_number_with_profiles(
            session, phone_number=employee_data.account_phone_number
        )

        if not account:
            account_schema = AccountCreate(
                phone_number=employee_data.account_phone_number,
                full_name=employee_data.account_full_name,
                email=employee_data.account_email,
                is_active=True,
            )
            account = await self.dao.account.create(session, obj_in=account_schema)

        # 2. Проверка существующей роли сотрудника для этого Account в этой Company
        existing_employee_role = (
            await self.dao.employee_role.get_by_account_id_and_company_id(
                session, account_id=account.id, company_id=company.id
            )
        )
        if existing_employee_role:
            raise EmployeeAlreadyExistsInCompanyException(
                employee_phone_number=employee_data.account_phone_number,
                company_id=company.id,
            )

        # 3. Проверка лимита сотрудников
        # company должен быть передан с загруженными subscriptions.tariff_plan
        current_sub = get_current_subscription(company)
        if current_sub and current_sub.tariff_plan:
            max_employees = current_sub.tariff_plan.max_employees
            if max_employees is not None and max_employees > 0:
                current_employee_count = (
                    await self.dao.employee_role.count_active_by_company_id(
                        session, company_id=company.id
                    )
                )
                if current_employee_count >= max_employees:
                    raise EmployeeLimitExceededException(
                        company_id=company.id, limit=max_employees
                    )

        # 4. Создать EmployeeRole. "Рабочие" поля по умолчанию берутся из Account.
        new_employee_role = await self.dao.employee_role.create_employee_role(
            session,
            account_id=account.id,
            company_id=company.id,
            position=employee_data.position,
            work_full_name=account.full_name,
            work_email=account.email,
            work_phone_number=account.phone_number,
        )

        # 5. Привязать к торговым точкам
        if employee_data.outlet_ids:
            outlets_to_assign = await self._validate_and_get_outlets_for_assignment(
                session, outlet_ids=employee_data.outlet_ids, company_id=company.id
            )

            await session.refresh(new_employee_role, ["assigned_outlets"])

            await self.dao.employee_role.set_assigned_outlets(
                session,
                employee_role=new_employee_role,
                outlets_to_assign=outlets_to_assign,
            )

        # 6. Загружаем EmployeeRole с деталями для ответа
        final_employee_role = await self.dao.employee_role.get_by_id_with_details(
            session, employee_role_id=new_employee_role.id
        )
        if not final_employee_role:  # Маловероятно, если создание прошло успешно
            raise EmployeeNotFoundException(identifier=new_employee_role.id)

        return await self._build_employee_response(session, final_employee_role)

    async def update_employee_in_company(
        self,
        session: AsyncSession,
        employee_role_to_update: EmployeeRoleModel,
        update_data: EmployeeUpdate,
    ) -> EmployeeResponse:

        employee_role_was_modified = False
        update_fields_for_role = update_data.model_dump(exclude_unset=True)

        # Обновление полей EmployeeRole
        if "position" in update_fields_for_role:
            if employee_role_to_update.position != update_fields_for_role["position"]:
                employee_role_to_update.position = update_fields_for_role["position"]
                employee_role_was_modified = True

        if "work_phone_number" in update_fields_for_role:
            new_work_phone = update_fields_for_role["work_phone_number"]
            if new_work_phone != employee_role_to_update.work_phone_number:
                if (
                    new_work_phone
                ):  # Проверка уникальности только если номер предоставлен и он не пустой
                    existing_work_phone_employee = (
                        await self.dao.employee_role.get_active_by_work_phone(
                            session, work_phone_number=new_work_phone
                        )
                    )
                    if (
                        existing_work_phone_employee
                        and existing_work_phone_employee.id
                        != employee_role_to_update.id
                    ):
                        raise ConflictException(
                            detail=f"The work phone number '{new_work_phone}' is already in use by another active employee."
                        )
                employee_role_to_update.work_phone_number = new_work_phone
                employee_role_was_modified = True

        # Обновляем привязку к торговым точкам, если передано (даже если это пустой список)
        outlets_updated = False
        if (
            update_data.outlet_ids is not None
        ):  # Используем update_data напрямую, т.к. model_dump может убрать None
            outlets_to_assign = await self._validate_and_get_outlets_for_assignment(
                session,
                outlet_ids=update_data.outlet_ids,
                company_id=employee_role_to_update.company_id,
            )

            await session.refresh(
                employee_role_to_update, ["account", "assigned_outlets"]
            )

            await self.dao.employee_role.set_assigned_outlets(
                session,
                employee_role=employee_role_to_update,
                outlets_to_assign=outlets_to_assign,
            )
            outlets_updated = True  # Флаг, что была операция с торговыми точками

        if employee_role_was_modified:
            session.add(employee_role_to_update)

        # assign_outlets_to_employee_role уже делает refresh для assigned_outlets.
        # Нам нужно убедиться, что employee_role_to_update содержит актуальные position и work_phone_number,
        # а также account (который не менялся) и обновленные assigned_outlets.
        # Метод get_by_id_with_details перезагрузит все это.

        # Если были изменения, или если просто хотим вернуть свежий объект с полными связями
        if employee_role_was_modified or outlets_updated:
            # Можно просто await session.refresh(employee_role_to_update, attribute_names=['account', 'assigned_outlets'])
            # если уверены, что все поля employee_role_to_update уже актуальны.
            # Но для полной гарантии и загрузки связей лучше так:
            updated_employee_role_for_response = (
                await self.dao.employee_role.get_by_id_with_details(
                    session, employee_role_id=employee_role_to_update.id
                )
            )
            if not updated_employee_role_for_response:  # Крайне маловероятно
                raise EmployeeNotFoundException(identifier=employee_role_to_update.id)
            return await self._build_employee_response(
                session, updated_employee_role_for_response
            )
        else:
            # Если изменений не было, все равно строим ответ из переданного объекта,
            # убедившись, что его связи загружены для _build_employee_response
            return await self._build_employee_response(session, employee_role_to_update)

    async def get_employees_for_company(
        self, session: AsyncSession, company_id: int, skip: int, limit: int
    ) -> List[EmployeeResponse]:
        employee_role_models = (
            await self.dao.employee_role.get_multi_by_company_id_with_details(
                session, company_id=company_id, skip=skip, limit=limit
            )
        )
        return [
            await self._build_employee_response(session, er)
            for er in employee_role_models
        ]

    async def get_employee_response_by_id(
        self, session: AsyncSession, employee_role: EmployeeRoleModel
    ) -> EmployeeResponse:
        """
        Формирует EmployeeResponse из предоставленного объекта EmployeeRoleModel.
        Предполагается, что employee_role уже получен и проверен на доступ
        зависимостью в эндпоинте (например, deps.get_owned_employee_role),
        и что он не является None и не мягко удален (если это не предполагается).
        """
        if not employee_role:  # Дополнительная проверка на None
            # Эта ситуация не должна возникать, если зависимость отработала корректно
            raise EmployeeNotFoundException(identifier=employee_role.id)

        return await self._build_employee_response(session, employee_role)

    async def remove_employee_from_company(
        self, session: AsyncSession, employee_role_to_remove: EmployeeRoleModel
    ) -> EmployeeResponse:
        archived_employee_role = await self.dao.employee_role.soft_delete(
            session, id_=employee_role_to_remove.id
        )
        if not archived_employee_role:
            raise EmployeeNotFoundException(identifier=employee_role_to_remove.id)

        final_employee_role = (
            await self.dao.employee_role.get_by_id_with_details_including_deleted(
                session, employee_role_id=archived_employee_role.id
            )
        )
        if not final_employee_role:
            await session.refresh(
                archived_employee_role, ["account", "assigned_outlets"]
            )
            return await self._build_employee_response(session, archived_employee_role)

        return await self._build_employee_response(session, final_employee_role)
