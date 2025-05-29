from pydantic import BaseModel

from backend.enums.back_office import \
    AdminAccessLevelEnum  # Убедитесь, что путь правильный


class UserRoleBase(BaseModel):
    access_level: AdminAccessLevelEnum

class UserRoleCreate(UserRoleBase):
    # account_id будет установлен в сервисе
    pass

class UserRoleUpdate(UserRoleBase):
    pass

class UserRoleResponse(UserRoleBase):
    id: int
    account_id: int
    # is_active: bool # У нас нет is_active в UserRole
    class Config:
        from_attributes = True
