from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDAO
from app.core.dependencies import get_broadcast_service, get_dao, get_owned_company, get_session
from app.models.company import Company
from app.schemas.broadcast import BroadcastCreate
from app.services.company_telegram_broadcast import BroadcastService

# Создаем новый роутер для эндпоинтов рассылок
router = APIRouter()


@router.post(
    "", # Путь относительно префикса, заданного в api.py (/companies/{company_id}/broadcasts)
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and queue a new broadcast",
    description=(
        "Принимает запрос на создание рассылки, "
        "сохраняет ее в БД и публикует задачу в очередь для асинхронной отправки. "
        "Возвращает ответ немедленно."
    )
)
async def create_broadcast(
    broadcast_in: BroadcastCreate,
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    broadcast_service: BroadcastService = Depends(get_broadcast_service),
):
    """
    Создает новую рассылку и ставит ее в очередь на отправку.

    - **broadcast_in**: Тело запроса с текстом сообщения.
    - **company**: Компания, от имени которой делается рассылка (проверяется владение).
    - **session**: Сессия базы данных.
    - **broadcast_service**: Сервис для управления логикой рассылок.
    """
    broadcast_task = await broadcast_service.create_and_send_broadcast(
        session=session,
        company_id=company.id,
        message_text=broadcast_in.message_text,
    )

    # Мы возвращаем статус 202 Accepted, что означает "Запрос принят к обработке,
    # но сама обработка еще не завершена". Это правильный паттерн для асинхронных операций.
    return {"status": "accepted", "broadcast_id": broadcast_task.broadcast_id}