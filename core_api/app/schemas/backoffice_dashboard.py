from typing import List, Optional

from pydantic import BaseModel, Field

from app.enums import CompanyStatusEnum
from app.schemas.account import (  # Предполагаем, что Enum'ы импортируются так
    AccountResponse,
)


class DashboardCompanyAdminResponse(BaseModel):
    """
    Схема для представления компании, которой пользователь владеет
    """

    id: int
    name: str
    status: CompanyStatusEnum
    legal_name: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardCompanyEmployeeResponse(BaseModel):
    """
    Схема для представления компании, в которой пользователь является сотрудником
    """

    id: int
    name: str
    employee_position: Optional[str] = (
        None  # Должность текущего пользователя в этой компании
    )
    company_status: CompanyStatusEnum  # Статус компании, где он работает

    class Config:
        from_attributes = True  # Потребуется адаптация при формировании данных


class DashboardResponse(BaseModel):
    """
    Основная схема ответа для эндпоинта
    """

    account_info: AccountResponse
    owned_companies: List[DashboardCompanyAdminResponse] = Field(default_factory=list)
    employee_in_companies: List[DashboardCompanyEmployeeResponse] = Field(
        default_factory=list
    )
    can_create_company: bool = True  # По умолчанию разрешаем, логика может быть сложнее
