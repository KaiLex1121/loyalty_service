from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuButtons:

    show_profile = InlineKeyboardButton(text="Профиль", callback_data="show_profile")

    find_customer = InlineKeyboardButton(text="Найти клиента", callback_data="find_customer")

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )

    logout = InlineKeyboardButton(text="Выйти", callback_data="logout")


class MainMenuKeyboards:

    main_window_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [MainMenuButtons.show_profile],
            [MainMenuButtons.find_customer],
            [MainMenuButtons.logout]
        ]
    )

    back_to_main_menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [MainMenuButtons.to_main_menu]
        ]
    )
