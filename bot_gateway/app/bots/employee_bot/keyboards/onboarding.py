from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict

class OnboardingButtons:

    share_contact = KeyboardButton(text="Поделиться контактом", request_contact=True)

    return_to_start = InlineKeyboardButton(
        text="Вернуться в начало", callback_data="return_to_start"
    )


class OnboardingKeyboards:

    share_contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[[OnboardingButtons.share_contact]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    return_to_start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[OnboardingButtons.return_to_start]]
    )

    @staticmethod
    def get_outlet_selection_keyboard(outlets: List[Dict]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for outlet in outlets:
            # В callback_data будем передавать префикс и ID точки
            builder.button(text=outlet['name'], callback_data=f"select_outlet:{outlet['id']}")
        builder.adjust(1) # По одной кнопке в ряд
        return builder.as_markup()
