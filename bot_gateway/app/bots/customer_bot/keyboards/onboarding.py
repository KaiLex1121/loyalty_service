from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


class OnboardingButtons:

    share_contact = KeyboardButton(text="Поделиться контактом", request_contact=True)

    accept_personal_data_consent = InlineKeyboardButton(
        text="Принять", callback_data="accept_personal_data_consent"
    )

    decline_personal_data_consent = InlineKeyboardButton(
        text="Отклонить", callback_data="decline_personal_data_consent"
    )

    next_step = InlineKeyboardButton(text="Далее", callback_data="next_onboarding_step")

    return_to_start = InlineKeyboardButton(
        text="Вернуться в начало", callback_data="return_to_start"
    )


class OnboardingKeyboards:

    personal_data_consent_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [OnboardingButtons.accept_personal_data_consent],
            [OnboardingButtons.decline_personal_data_consent],
        ]
    )

    next_step_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[OnboardingButtons.next_step]]
    )

    share_contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[[OnboardingButtons.share_contact]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return_to_start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[OnboardingButtons.return_to_start]]
    )
