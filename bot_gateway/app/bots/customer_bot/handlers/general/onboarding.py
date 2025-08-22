from typing import Union
from aiogram import F, Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards

from app.bots.customer_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.customer_bot.states.general import OnboardingDialogStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter
from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))



@router.message(CommandStart())
@router.callback_query(F.data == "return_to_start")
async def handle_pressing_start(
    event: Union[Message, CallbackQuery], company_id: int, company_name: str, state: FSMContext, api_client: CoreApiClient
):
    telegram_id = event.from_user.id

    # 1. Проверяем, зарегистрирован ли уже пользователь
    customer_profile = await api_client.get_customer_profile(
        telegram_id, company_id
    )

    if isinstance(event, Message):
        if customer_profile:
            # Сценарий А: Пользователь найден
            await event.answer(
                f"С возвращением в программу лояльности «{company_name}»!\n\n"
                "Вы можете просмотреть свой профиль или перейти к другим функциям.",
                reply_markup=MainMenuKeyboards.main_window_keyboard,
            )
        else:
            # Сценарий Б: Новый пользователь
            await event.answer(
                text=f"Добро пожаловать в программу лояльности «{company_name}»!\n\n"
                "Мы заботимся о вашей приватности, поэтому вы можете ознакомиться с политикой конфиденциальности по ссылке: <ссылка на политику конфиденциальности>.",
                reply_markup=OnboardingKeyboards.next_step_keyboard,
            )
    else:
        await event.message.edit_text(
            text=f"Добро пожаловать в программу лояльности «{company_name}»!\n\n"
            "Мы заботимся о вашей приватности, поэтому вы можете ознакомиться с политикой конфиденциальности по ссылке: <ссылка на политику конфиденциальности>.",
            reply_markup=OnboardingKeyboards.next_step_keyboard,
        )


@router.callback_query(F.data == "next_onboarding_step")
async def handle_pressing_next_step(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Нажимая кнопку «Согласен», вы разрешаете нам использовать ваш номер телефона для отправки вам уведомлений.",
        reply_markup=OnboardingKeyboards.personal_data_consent_keyboard,
    )


@router.callback_query(F.data == "accept_personal_data_consent")
async def handle_pressing_accept_personal_data_consent(
    callback: CallbackQuery, state: FSMContext
):
    await callback.message.answer(
        text="Спасибо. Теперь, пожалуйста, поделитесь своим номером телефона.",
        reply_markup=OnboardingKeyboards.share_contact_keyboard,
    )
    await state.set_state(OnboardingDialogStates.WAITING_FOR_THE_NUMBER)


@router.callback_query(F.data == "decline_personal_data_consent")
async def handle_pressing_decline_personal_data_consent(
    callback: CallbackQuery, state: FSMContext
):
    await callback.message.edit_text(
        text="Без вашего согласия мы не можем продолжить.",
        reply_markup=OnboardingKeyboards.return_to_start_keyboard,
    )
    await state.set_state(OnboardingDialogStates.WAITING_FOR_ACCEPTANCE)


@router.message(F.contact, StateFilter(OnboardingDialogStates.WAITING_FOR_THE_NUMBER))
async def handle_pressing_share_contact(message: types.Message, company_id: int, state: FSMContext, api_client: CoreApiClient):
    """
    Хендлер, который срабатывает, когда пользователь делится своим контактом.
    """
    contact = message.contact

    try:
        # 2. Регистрируем пользователя через Core API
        await api_client.onboard_customer(
            telegram_id=contact.user_id,
            phone_number=contact.phone_number,
            company_id=company_id,
            full_name=message.from_user.full_name,
        )

        # 3. Отправляем подтверждение и убираем кастомную клавиатуру
        await message.answer(
            "Спасибо. Вы успешно зарегистрированы!",
            reply_markup=MainMenuKeyboards.main_window_keyboard,
        )
        await state.set_state(OnboardingDialogStates.WAITING_FOR_THE_NUMBER)

    except Exception as e:
        # Обработка ошибок (например, Core API недоступен)
        await message.answer(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        print(f"Onboarding failed for user {contact.user_id}: {e}")


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_THE_NUMBER))
async def handle_waiting_for_the_number(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, поделитесь своим номером телефона.",
        reply_markup=OnboardingKeyboards.share_contact_keyboard,
    )
