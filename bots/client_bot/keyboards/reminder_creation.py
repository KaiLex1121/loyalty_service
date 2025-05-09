from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class ReminderCreationButtons:
    daily_reminder = InlineKeyboardButton(text="Ежедневно", callback_data="daily")

    weekly_reminder = InlineKeyboardButton(text="Еженедельно", callback_data="weekly")

    monthly_reminder = InlineKeyboardButton(text="Ежемесячно", callback_data="monthly")

    yearly_reminder = InlineKeyboardButton(text="Ежегодно", callback_data="yearly")

    custom_reminder_type = InlineKeyboardButton(text="Другое", callback_data="other")

    start_reminder_now = InlineKeyboardButton(text="Сейчас", callback_data="start_now")

    start_reminder_other_time = InlineKeyboardButton(
        text="В другое время", callback_data="start_another_time"
    )
    confirm_reminder_creation = InlineKeyboardButton(
        text="Подтвердить создание напоминания",
        callback_data="confirm_reminder_creation",
    )

    to_main_menu = InlineKeyboardButton(
        text="В главное меню", callback_data="to_main_menu"
    )


class ReminderCreationKeyboards:
    choose_reminder_type = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ReminderCreationButtons.daily_reminder,
                ReminderCreationButtons.weekly_reminder,
            ],
            [
                ReminderCreationButtons.monthly_reminder,
                ReminderCreationButtons.yearly_reminder,
            ],
            [ReminderCreationButtons.custom_reminder_type],
            [ReminderCreationButtons.to_main_menu],
        ]
    )

    choose_reminder_start_time = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                ReminderCreationButtons.start_reminder_now,
                ReminderCreationButtons.start_reminder_other_time,
            ],
            [ReminderCreationButtons.to_main_menu],
        ]
    )

    to_main_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [ReminderCreationButtons.to_main_menu],
        ]
    )

    confirm_reminder_creation = InlineKeyboardMarkup(
        inline_keyboard=[
            [ReminderCreationButtons.confirm_reminder_creation],
            [ReminderCreationButtons.to_main_menu],
        ]
    )
