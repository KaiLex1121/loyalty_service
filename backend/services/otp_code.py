from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate


class OtpCodeService:

    async def invalidate_previous_otps(
        self, db: AsyncSession, dao: HolderDAO, account: Account, purpose: str
    ) -> None:
        try:
            await dao.otp_code.invalidate_previous_otps(
                db,
                account_id=account.id,
                purpose=purpose,
                phone_number_ref=account.phone_number
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )


    async def create_otp(
        self,
        db: AsyncSession,
        dao: HolderDAO,
        *,
        hashed_otp: str,
        expires_at: datetime,
        purpose: str,
        account: Account
    ):
        await dao.otp_code.create_otp(db,
            hashed_otp=hashed_otp,
            expires_at=expires_at,
            purpose=purpose,
            account_id=account.id
        )
        await db.commit()
