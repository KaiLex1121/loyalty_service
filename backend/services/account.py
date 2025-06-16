from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.exceptions import InternalServerError  # Для непредвиденных ошибок DAO
from backend.exceptions import (  # Импортируем из __init__.py exceptions
    AccountCreationException,
    AccountNotFoundException,
    AccountUpdateException,
)
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    async def get_account_by_phone(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> Optional[Account]:
        result = await dao.account.get_by_phone_number_without_relations(
            db, phone_number=phone_number
        )
        return result

    async def get_account_by_id(
        self, db: AsyncSession, dao: HolderDAO, account_id: int
    ) -> Account:
        account = await dao.account.get(db, id_=account_id)
        if not account:
            raise AccountNotFoundException(
                identifier=account_id,
                identifier_type="ID",
                internal_details={"requested_by": "get_account_by_id"},
            )
        return account

    async def create_account_by_phone(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        phone_number: str,
        email: Optional[str] = None,
    ) -> Account:
        try:
            account_in_create = AccountCreate(
                phone_number=phone_number, email=email, is_active=False
            )
            account = await dao.account.create(db, obj_in=account_in_create)
            return account
        except Exception as e:  # Ловим общую ошибку от DAO/DB
            # Здесь можно добавить проверку на конкретные ошибки БД (e.g., IntegrityError для дубликатов)
            # и рейзить AccountAlreadyExistsException, если нужно.
            # Пока оставим как общую ошибку создания.
            raise AccountCreationException(
                reason=str(e),
                internal_details={
                    "phone_number": phone_number,
                    "email": email,
                    "original_error_type": type(e).__name__,
                    "original_error_message": str(e),
                },
            )

    async def get_account(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> Account | None:
        account = await self.get_account_by_phone(db, dao, phone_number=phone_number)
        return account

    async def set_account_as_active(self, account: Account) -> Account:
        account.is_active = True
        return account

    async def update_account(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        account_db: Account,
        account_in: AccountUpdate,
    ) -> Account:
        try:
            updated_account = await dao.account.update(
                session=session, db_obj=account_db, obj_in=account_in
            )
            await session.flush()  # flush может вызвать ошибки Constraints
            await session.refresh(updated_account)
            return updated_account
        except Exception as e:  # Ловим общую ошибку от DAO/DB
            raise AccountUpdateException(
                account_id=account_db.id,
                reason=str(e),
                internal_details={
                    "update_data": account_in.model_dump(exclude_unset=True),
                    "original_error_type": type(e).__name__,
                    "original_error_message": str(e),
                },
            )
