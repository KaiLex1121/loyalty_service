from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from backend.core.dependencies import authenticate_bot_and_get_company
from backend.enums.telegram_bot_enums import BotTypeEnum

router = APIRouter()


# Pydantic модель для входящих данных от Telegram (можно расширить)
class TelegramUpdate(BaseModel):
    update_id: int
    # ... другие поля из объекта Update от Telegram


@router.post(
    "/telegram/bot{token}",
    summary="Webhook for Telegram Bots",
    description="Единая точка входа для всех Telegram-ботов. Бот идентифицируется по токену в URL.",
)
async def handle_telegram_webhook(
    update: TelegramUpdate,
    request: Request,
    token: str,  # FastAPI автоматически извлечет {token} из пути
    bot_data: tuple[int, BotTypeEnum] = Depends(authenticate_bot_and_get_company),
):
    company_id, bot_type = bot_data

    # Здесь будет основная логика маршрутизации
    # Например, передача `update` в соответствующий сервис в зависимости от `bot_type`
    # if bot_type == BotTypeEnum.CUSTOMER:
    #     await customer_bot_service.process_update(update, company_id)
    # elif bot_type == BotTypeEnum.EMPLOYEE:
    #     await employee_bot_service.process_update(update, company_id)

    return {"status": "ok", "company_id": company_id, "bot_type": bot_type.value}
