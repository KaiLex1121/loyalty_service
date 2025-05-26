from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    async def get_account_by_phone(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> Optional[Account]:
        return await dao.account.get_by_phone_number(db, phone_number=phone_number)

    async def get_account_by_id(
        self, db: AsyncSession, dao: HolderDAO, account_id: int
    ) -> Optional[Account]:
        account = await dao.account.get(db, account_id=account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="account not found"
            )
        return account

    async def create_account(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        phone_number: str,
        email: Optional[str] = None,
    ) -> Account:
        account_in_create = AccountCreate(
            phone_number=phone_number, email=email, is_active=False
        )
        account = await dao.account.create(db, obj_in=account_in_create)
        return account

    async def get_or_create_account(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> Account:
        account = await self.get_account_by_phone(db, dao, phone_number=phone_number)
        if not account:
            account = await self.create_account(db, dao, phone_number=phone_number)
        await db.flush()
        await db.refresh(account)
        return account

    async def update_account(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        account: Account,
        account_in: AccountUpdate,
    ) -> Account:
        updated_account = await dao.account.update(
            db, db_obj=account, obj_in=account_in
        )
        await db.flush()
        await db.refresh(updated_account)
        return updated_account
