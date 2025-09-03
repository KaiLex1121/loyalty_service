from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class CashbackAccrualButtons:

    to_confirm_cashback_accrual = InlineKeyboardButton(
        text="Далее", callback_data="to_confirm_cashback_accrual"
    )

    confirm_cashback_accrual = InlineKeyboardButton(
        text="Подтвердить", callback_data="confirm_cashback_accrual"
    )

    cancel_cashback_accrual = InlineKeyboardButton(
        text="Отменить", callback_data="cancel_cashback_accrual"
    )


class CashbackAccrualKeyboards:

    to_confirm_cashback_accrual_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [CashbackAccrualButtons.to_confirm_cashback_accrual],
            [CashbackAccrualButtons.cancel_cashback_accrual],
        ]
    )

    confirm_cashback_accrual_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [CashbackAccrualButtons.confirm_cashback_accrual],
            [CashbackAccrualButtons.cancel_cashback_accrual],
        ]
    )
