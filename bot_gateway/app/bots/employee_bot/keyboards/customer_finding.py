from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class CustomerFindingButtons:

    accrue_cashback = InlineKeyboardButton(
        text="Начислить", callback_data="accrue_cashback"
    )

    spend_cashback = InlineKeyboardButton(
        text="Списать", callback_data="spend_cashback"
    )

    transaction_history = InlineKeyboardButton(
        text="История операций", callback_data="transaction_history"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )


class CustomerFindingKeyboards:

    customer_finding_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                CustomerFindingButtons.accrue_cashback,
                CustomerFindingButtons.spend_cashback,
            ],
            [CustomerFindingButtons.transaction_history],
            [CustomerFindingButtons.to_main_menu],
        ]
    )

    customer_not_found_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [CustomerFindingButtons.to_main_menu],
        ]
    )
