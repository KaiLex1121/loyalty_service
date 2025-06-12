from pydantic import BaseModel

from backend.enums.back_office import (  # Убедитесь, что путь правильный
    UserAccessLevelEnum,
)


class UserRoleBase(BaseModel):
    access_level: UserAccessLevelEnum


class UserRoleCreate(UserRoleBase):
    account_id: int


class UserRoleUpdate(UserRoleBase):
    pass


class UserRoleResponse(UserRoleBase):
    id: int
    account_id: int

    # is_active: bool # У нас нет is_active в UserRole
    class Config:
        from_attributes = True
