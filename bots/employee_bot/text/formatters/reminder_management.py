from src.dto.reminder import GetReminderToShowDTO
from src.text.formatters.general import (format_custom_frequency_to_russian,
                                         format_reminder_enum_value_to_russian)
from src.utils.datetime_utils import convert_dt_to_russian


def get_formatted_reminder_text(reminder: GetReminderToShowDTO):
    text = reminder.text
    default_frequency = reminder.frequency_type.value
    custom_frequency = (
        format_custom_frequency_to_russian(reminder.custom_frequency)
        if reminder.custom_frequency
        else None
    )
    frequency = custom_frequency if custom_frequency is not None else default_frequency
    next_run_time = (
        "напоминание отключено"
        if reminder.next_run_time is None
        else convert_dt_to_russian(reminder.next_run_time)
    )
    status = "активен" if reminder.is_active else "неактивен"

    formated_text = (
        "Информация о напоминании:\n",
        f"Текст: {text}",
        f"Статус: {status}",
        f"Периодичность напоминания: {frequency}",
        f"Время следующего срабатывания: {next_run_time}",
    )

    return "\n\n".join(formated_text)
