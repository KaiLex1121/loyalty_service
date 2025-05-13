from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.user import User

class UserDAO(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)