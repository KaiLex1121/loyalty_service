from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuButtons:

    create_reminder = InlineKeyboardButton(
        text="Создать напоминание", callback_data="create_reminder"
    )

    show_created_reminders = InlineKeyboardButton(
        text="Мои напоминания", callback_data="show_created_reminders"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )


class MainMenuKeyboards:

    main_window = InlineKeyboardMarkup(
        inline_keyboard=[
            [MainMenuButtons.create_reminder],
            [MainMenuButtons.show_created_reminders],
        ]
    )
