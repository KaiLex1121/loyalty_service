# backend/exceptions/services/loyalty.py
import decimal
from typing import Optional  # Добавил Optional
from backend.exceptions.common import BadRequestException


class InsufficientCashbackBalanceException(BadRequestException):
    def __init__(
        self,
        current_balance: decimal.Decimal,
        requested_spend: Optional[decimal.Decimal] = None,
        detail: Optional[str] = None,
    ):
        if not detail:
            if requested_spend is not None:
                detail = f"Недостаточно средств для списания. Баланс: {current_balance}, запрашивается: {requested_spend}."
            else:
                detail = f"На балансе клиента недостаточно средств (текущий баланс: {current_balance})."


class InvalidSpendAmountException(BadRequestException):
    pass  # Сообщение будет передано из сервиса


class CashbackAccrualFailedException(BadRequestException): # 400 Bad Request
    detail = "Не удалось начислить кэшбэк."

class CashbackSpendFailedException(BadRequestException):
    """Вызывается, когда операция списания не может быть завершена из-за внутренней ошибки."""
    detail = "Не удалось списать кэшбэк."
