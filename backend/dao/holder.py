from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.user import UserDAO


@dataclass
class HolderDAO:
    user: UserDAO = field(init=False)

    def __post_init__(self):
        self.user = UserDAO()
