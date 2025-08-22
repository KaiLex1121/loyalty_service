from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.bots.employee_bot.keyboards.main_menu import MainMenuButtons


class ViewProfileButtons:

    show_balance = InlineKeyboardButton(text="Мой баланс", callback_data="show_balance")

    show_operations = InlineKeyboardButton(
        text="Мои операции", callback_data="show_operations"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )

    logout = InlineKeyboardButton(text="Выйти из профиля", callback_data="logout")


class ViewProfileKeyboards:

    view_profile_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [ViewProfileButtons.logout],
            [ViewProfileButtons.to_main_menu],
        ]
    )
