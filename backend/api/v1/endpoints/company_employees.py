from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_employee_service,
    get_owned_company,
    get_owned_employee_role,
    get_session,
)
from backend.models.company import Company as CompanyModel
from backend.models.employee_role import EmployeeRole
from backend.models.outlet import Outlet as OutletModel
from backend.schemas.company_employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from backend.schemas.company_outlet import OutletCreate, OutletResponse, OutletUpdate
from backend.services.company_employee import EmployeeService
from backend.services.company_outlet import OutletService

router = APIRouter()


@router.get(
    "/{company_id}/employees/{employee_role_id}",
    response_model=EmployeeResponse,
    summary="Get specific company employee",
)
async def get_company_employee(
    employee_role: EmployeeRole = Depends(get_owned_employee_role),
    session: AsyncSession = Depends(get_session),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """Returns detailed information about specific company employee."""
    return await employee_service.get_employee_response_by_id(session, employee_role)


@router.post(
    "/{company_id}/employees",  # Путь для создания в контексте компании
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить нового сотрудника в компанию",
    description="Создает аккаунт для сотрудника (если его нет) и его роль в указанной компании. Привязывает к торговым точкам.",
)
async def add_employee_to_company_endpoint(
    employee_data: EmployeeCreate,
    company: CompanyModel = Depends(
        get_owned_company
    ),  # Зависимость проверяет доступ к company_id и возвращает объект Company
    session: AsyncSession = Depends(get_session),  # Сессия нужна сервису для транзакции
    employee_service: EmployeeService = Depends(
        get_employee_service
    ),  # Инжектим сервис
):
    return await employee_service.add_employee_to_company(
        session, company, employee_data
    )


@router.get(
    "/{company_id}/employees",
    response_model=List[EmployeeResponse],
    summary="Получить список сотрудников компании",
)
async def get_company_employees_endpoint(
    company: CompanyModel = Depends(get_owned_company),  # Проверка доступа к company_id
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Возвращает список сотрудников для указанной компании, к которой текущий пользователь имеет доступ.
    """
    return await employee_service.get_employees_for_company(
        session, company.id, skip, limit
    )


@router.get(
    "/{company_id}/employees/{employee_role_id}",  # Отдельный путь для конкретного EmployeeRole
    response_model=EmployeeResponse,
    summary="Получить информацию о конкретном сотруднике",
)
async def get_employee_by_id_endpoint(
    employee_role: EmployeeRole = Depends(get_owned_employee_role),
    session: AsyncSession = Depends(
        get_session
    ),  # Может понадобиться сервису для _build_employee_response
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Возвращает детальную информацию о сотруднике, если текущий пользователь
    имеет доступ к компании этого сотрудника.
    """
    return await employee_service.get_employee_response_by_id(session, employee_role)


@router.put(
    "/{company_id}/employees/{employee_role_id}",
    response_model=EmployeeResponse,
    summary="Обновить информацию о сотруднике",
)
async def update_employee_endpoint(
    update_data: EmployeeUpdate,
    employee_role_to_update: EmployeeRole = Depends(
        get_owned_employee_role
    ),  # Зависимость
    session: AsyncSession = Depends(get_session),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Обновляет данные сотрудника (его роль в компании и, возможно, некоторые данные Account).
    Доступно владельцу компании этого сотрудника или системному администратору.
    """

    return await employee_service.update_employee_in_company(
        session, employee_role_to_update, update_data
    )


@router.delete(
    "/{company_id}/employees/{employee_role_id}",
    response_model=EmployeeResponse,
    summary="Архивировать (мягко удалить) сотрудника из компании",
)
async def archive_employee_endpoint(
    employee_role_to_remove: EmployeeRole = Depends(
        get_owned_employee_role
    ),  # Зависимость
    session: AsyncSession = Depends(get_session),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Мягко удаляет роль сотрудника в компании (устанавливает deleted_at).
    Сам Account сотрудника не удаляется.
    """

    return await employee_service.remove_employee_from_company(
        session, employee_role_to_remove
    )
