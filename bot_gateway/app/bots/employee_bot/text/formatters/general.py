from datetime import datetime


def format_transaction_history(transactions: list[dict]) -> str:
    if not transactions:
        return "История операций пуста."

    history_parts = []
    for i, tx in enumerate(transactions, 1):
        tx_time = datetime.fromisoformat(tx["transaction_time"])

        if tx["transaction_type"] == "ACCRUAL_PURCHASE":
            title = f"✅ Начисление за покупку"
            details = f"Начислено баллов: <b>{tx['cashback_accrued']}</b>"
        elif tx["transaction_type"] == "SPENDING_PURCHASE":
            title = f"💳 Списание в счет покупки"
            details = f"Списано баллов: <b>{tx['cashback_spent']}</b>"
        else:
            title = f"⚙️ Другая операция"
            details = ""

        part = (
            f"<b>{i}. {title}</b>\n"
            f"Дата: {tx_time.strftime('%d.%m.%Y')}\n"
            f"Время: {tx_time.strftime('%H:%M')}\n"
            f"{details}\n"
            f"Баланс после: <b>{tx['balance_after']}</b>"
        )
        history_parts.append(part)

    return "\n\n".join(history_parts)


def format_promotions(promotions: list[dict]) -> list[str]:
    if not promotions:
        return ["На данный момент активных акций нет."]

    promo_messages = []
    for promo in promotions:
        # TODO: Добавить больше деталей из cashback_config
        message = (
            f"🎁 <b>{promo['name']}</b>\n\n"
            f"{promo.get('description', 'Подробности у кассира.')}"
        )
        promo_messages.append(message)

    return promo_messages



def format_customer_profile_for_employee(customer: dict) -> str:
    """Форматирует профиль клиента для отображения сотруднику."""
    full_name = customer.get("account", {}).get("full_name") or "Имя не указано"
    phone_number = customer.get("account", {}).get("phone_number")

    text = (
        f"👤 <b>Профиль клиента</b>\n\n"
        f"<b>ФИО:</b> {full_name}\n"
        f"<b>Телефон:</b> {phone_number}\n"
        f"<b>Баланс:</b> {customer['cashback_balance']} баллов"
    )
    return text