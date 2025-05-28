from pydantic import BaseModel

from backend.enums.back_office import \
    AdminAccessLevelEnum  # Убедитесь, что путь правильный


class UserRoleCreateInternal(BaseModel):
    account_id: int
    access_level: AdminAccessLevelEnum = AdminAccessLevelEnum.COMPANY_OWNER
    is_active: bool = True  # При создании через этот флоу, UserRole сразу активен
