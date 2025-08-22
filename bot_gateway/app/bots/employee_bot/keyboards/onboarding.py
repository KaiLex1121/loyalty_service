from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class OnboardingButtons:

    share_contact = KeyboardButton(
        text="Поделиться контактом", request_contact=True
    )

    return_to_start = InlineKeyboardButton(text="Вернуться в начало", callback_data="return_to_start")

class OnboardingKeyboards:

    share_contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[[OnboardingButtons.share_contact]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    return_to_start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[OnboardingButtons.return_to_start]]
    )