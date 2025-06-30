import httpx
from fastapi import status

from backend.core.logger import get_logger
from backend.exceptions.common import ServiceUnavailableException

logger = get_logger(__name__)


class TelegramIntegrationService:
    def __init__(self, base_url: str = "https://api.telegram.org"):
        self.base_url = base_url

    async def set_webhook(self, bot_token: str, webhook_url: str) -> None:
        """Устанавливает вебхук для бота через Telegram API."""
        url = f"{self.base_url}/bot{bot_token}/setWebhook"
        params = {"url": webhook_url}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()

                response_data = response.json()
                if not response_data.get("ok"):
                    logger.error(
                        f"Telegram API error on setWebhook: {response_data.get('description')}"
                    )
                    raise ServiceUnavailableException(
                        detail=f"Failed to set webhook: {response_data.get('description')}"
                    )
                logger.info(
                    f"Webhook successfully set for bot token ending in ...{bot_token[-4:]}"
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error setting webhook: {e.response.text}")
                raise ServiceUnavailableException(
                    detail="Failed to communicate with Telegram API."
                )
            except httpx.RequestError as e:
                logger.error(f"Request error setting webhook: {e}")
                raise ServiceUnavailableException(
                    detail="Network error while contacting Telegram API."
                )

    async def delete_webhook(self, bot_token: str) -> None:
        """Удаляет вебхук для бота."""
        url = f"{self.base_url}/bot{bot_token}/deleteWebhook"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                logger.info(
                    f"Webhook successfully deleted for bot token ending in ...{bot_token[-4:]}"
                )
            except httpx.RequestError:
                # Не бросаем ошибку, т.к. удаление вебхука - некритичная операция
                logger.warning(
                    f"Failed to delete webhook for bot token ...{bot_token[-4:]}. Might need manual removal."
                )
