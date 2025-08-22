from app.dao.holder import HolderDAO
from app.exceptions.common import NotFoundException
from app.publishers import broadcast_publisher
from app.schemas.broadcast import BroadcastCreateInternal
from sqlalchemy.ext.asyncio import AsyncSession

from shared.enums.telegram_bot_enums import BotTypeEnum
from shared.schemas.schemas import BroadcastTask  # <-- ИСПОЛЬЗУЕМ ОБЩУЮ СХЕМУ


class BroadcastService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def create_and_send_broadcast(
        self, session: AsyncSession, company_id: int, message_text: str
    ) -> BroadcastTask:
        customer_bot = await self.dao.telegram_bot.get_by_company_and_type(
            session, company_id=company_id, bot_type=BotTypeEnum.CUSTOMER
        )
        if not customer_bot:
            raise NotFoundException(
                detail="Active customer bot not found for this company."
            )

        user_ids = await self.dao.customer_role.get_telegram_user_ids_by_company(
            session, company_id
        )
        if not user_ids:
            raise NotFoundException(
                detail="No customers with Telegram ID found for broadcast."
            )

        broadcast_scheme = BroadcastCreateInternal(
            message_text=message_text, company_id=company_id
        )
        broadcast_db = await self.dao.broadcast.create(session, obj_in=broadcast_scheme)

        task = BroadcastTask(
            broadcast_id=broadcast_db.id,
            bot_token=customer_bot.token,
            user_ids=user_ids,
            message_text=message_text,
        )

        await broadcast_publisher.publish(task)

        return task
