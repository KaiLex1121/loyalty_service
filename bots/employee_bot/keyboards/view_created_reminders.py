from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class ViewCreatedRemindersButtons:

    show_all_reminders = InlineKeyboardButton(
        text="Все созданные напоминания",
        callback_data="show_all_reminders_list",  # show_all_reminders
    )

    show_active_reminders = InlineKeyboardButton(
        text="Активные", callback_data="show_active_reminders_list"
    )

    show_disabled_reminders = InlineKeyboardButton(
        text="Неактивные", callback_data="show_disabled_reminders_list"
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )

    delete_all_reminders = InlineKeyboardButton(
        text="Удалить все напоминания", callback_data="delete_all_reminders"
    )

    delete_all_active_reminders = InlineKeyboardButton(
        text="Удалить все активные напоминания",
        callback_data="delete_all_active_reminders",
    )

    delete_all_disabled_reminders = InlineKeyboardButton(
        text="Удалить все неактивные напоминания",
        callback_data="delete_all_disabled_reminders",
    )

    enable_all_disabled_reminders = InlineKeyboardButton(
        text="Включить все неактивные напоминания",
        callback_data="enable_all_disabled_reminders",
    )

    disable_all_active_reminders = InlineKeyboardButton(
        text="Отключить все активные напоминания",
        callback_data="disable_all_active_reminders",
    )


class ViewCreatedRemindersKeyboards:

    show_created_reminders = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ViewCreatedRemindersButtons.show_all_reminders,
            ],
            [
                ViewCreatedRemindersButtons.show_active_reminders,
                ViewCreatedRemindersButtons.show_disabled_reminders,
            ],
            [ViewCreatedRemindersButtons.to_main_menu],
        ],
    )

    show_all_reminders_management = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ViewCreatedRemindersButtons.delete_all_reminders,
            ],
            [
                ViewCreatedRemindersButtons.disable_all_active_reminders,
                ViewCreatedRemindersButtons.enable_all_disabled_reminders,
            ],
            [ViewCreatedRemindersButtons.to_main_menu],
        ],
    )

    show_active_reminders_management = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ViewCreatedRemindersButtons.delete_all_active_reminders,
                ViewCreatedRemindersButtons.disable_all_active_reminders,
            ],
            [ViewCreatedRemindersButtons.to_main_menu],
        ],
    )

    show_disabled_reminders_management = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ViewCreatedRemindersButtons.delete_all_disabled_reminders,
                ViewCreatedRemindersButtons.enable_all_disabled_reminders,
            ],
            [ViewCreatedRemindersButtons.to_main_menu],
        ],
    )
