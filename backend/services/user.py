from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.models.user import User
from backend.schemas.user import UserCreate, UserInDBBase, UserUpdate


class UserService:
    async def get_user_by_phone(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> Optional[User]:
        return await dao.user.get_by_phone_number(db, phone_number=phone_number)

    async def get_user_by_id(
        self, db: AsyncSession, dao: HolderDAO, user_id: int
    ) -> Optional[User]:
        user = await dao.user.get(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def create_user(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        phone_number: str,
        email: Optional[str] = None,
    ) -> User:
        user_in_create = UserCreate(
            phone_number=phone_number, email=email, is_active=False
        )
        user = await dao.user.create(db, obj_in=user_in_create)
        await db.commit()
        await db.refresh(user)
        return user

    async def get_or_create_user_for_otp(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> User:
        user = await self.get_user_by_phone(db, dao, phone_number=phone_number)
        if not user:
            user = await self.create_user(db, dao, phone_number=phone_number)
        return user

    async def set_otp_for_user(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        user: User,
        otp_code: str,
        otp_expires_at: datetime,
    ) -> User:
        user_update_data = UserUpdate(otp_code=otp_code, otp_expires_at=otp_expires_at)
        updated_user = await dao.user.update(db, db_obj=user, obj_in=user_update_data)
        await db.commit()
        await db.refresh(updated_user)
        return updated_user

    async def activate_user_and_clear_otp(
        self, db: AsyncSession, dao: HolderDAO, user: User
    ) -> User:
        update_data = {"otp_code": None, "otp_expires_at": None}
        if not user.is_active:
            update_data["is_active"] = True

        user_update_obj = UserUpdate(**update_data)
        updated_user = await dao.user.update(db, db_obj=user, obj_in=user_update_obj)
        await db.commit()
        await db.refresh(updated_user)
        return updated_user

    async def update_user(
        self, db: AsyncSession, dao: HolderDAO, user: User, user_in: UserUpdate
    ) -> User:
        updated_user = await dao.user.update(db, db_obj=user, obj_in=user_in)
        await db.commit()
        await db.refresh(updated_user)
        return updated_user
