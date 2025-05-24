from src.text.formatters.general import (format_custom_frequency_to_russian,
                                         format_reminder_enum_value_to_russian)
from src.utils.datetime_utils import convert_dt_to_russian


def get_formateed_confirmation_text(data: dict) -> str:

    text = data.get("text")
    default_frequency = format_reminder_enum_value_to_russian(
        data.get("frequency_type")
    )
    custom_frequency = (
        format_custom_frequency_to_russian(data.get("custom_frequency"))
        if data.get("custom_frequency")
        else None
    )
    frequency = custom_frequency if custom_frequency is not None else default_frequency
    start_dt = convert_dt_to_russian(data.get("start_datetime"))

    confirmation_lines = (
        "Пожалуйста, подтвердите данные напоминания:\n",
        f"Текст: {text}",
        f"Периодичность напоминания: {frequency}",
        f"Время начала: {start_dt}",
    )

    return "\n\n".join(confirmation_lines)
