from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuButtons:

    show_profile = InlineKeyboardButton(text="Профиль", callback_data="show_profile")

    show_promotions = InlineKeyboardButton(
        text="Мои акции", callback_data="show_promotions"
    )

    show_privacy_policy = InlineKeyboardButton(
        text="Политика конфиденциальности", callback_data="show_privacy_policy"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )


class MainMenuKeyboards:

    main_window_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [MainMenuButtons.show_profile],
            [MainMenuButtons.show_promotions],
            [MainMenuButtons.show_privacy_policy],
        ]
    )

    back_to_main_menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [MainMenuButtons.to_main_menu]
        ]
    )
