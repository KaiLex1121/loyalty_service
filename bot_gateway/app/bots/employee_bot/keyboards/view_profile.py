from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class ViewProfileButtons:

    show_balance = InlineKeyboardButton(text="Мой баланс", callback_data="show_balance")

    show_operations = InlineKeyboardButton(
        text="Мои операции", callback_data="show_operations"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )


class ViewProfileKeyboards:

    view_profile_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [ViewProfileButtons.show_balance],
            [ViewProfileButtons.show_operations],
            [ViewProfileButtons.to_main_menu],
        ]
    )
