from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class HolderDAO:
    session: AsyncSession
    user: UserDAO = field(init=False)

    def __post_init__(self):
        self.user = UserDAO(self.session)
