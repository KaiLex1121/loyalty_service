from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import BaseDAO
from backend.db.models import User

class UserDAO(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)