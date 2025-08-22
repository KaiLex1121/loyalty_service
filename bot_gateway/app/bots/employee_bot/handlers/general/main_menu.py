from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.api_client import CoreApiClient
from app.bots.employee_bot.filters.employee_auth import EmployeeAuthFilter
from app.bots.employee_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.keyboards.view_profile import ViewProfileKeyboards
from app.bots.employee_bot.states.general import (
    MainDialogStates,
    OnboardingDialogStates,
)
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.callback_query(F.data == "to_main_menu")
async def render_main_menu(callback: CallbackQuery, bot: Bot, state: FSMContext):
    text = "Вы вернулись в главное меню.\nВыберите действие"
    try:
        await callback.message.edit_text(
            text=text, reply_markup=MainMenuKeyboards.main_window_keyboard
        )
    except TelegramBadRequest:
        await callback.answer(
            text=text, reply_markup=MainMenuKeyboards.main_window_keyboard
        )
    await state.set_state(MainDialogStates.WAITING_IN_MAIN_MENU)


@router.callback_query(F.data == "show_profile")
async def handle_show_profile(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    company_id: int,
    api_client: CoreApiClient,
):
    profile = await api_client.get_customer_profile(callback.from_user.id, company_id)
    if profile:
        await callback.message.edit_text(
            f"Ваш профиль:", reply_markup=ViewProfileKeyboards.view_profile_keyboard
        )
    else:
        await callback.message.edit_text(
            "Не удалось получить ваш профиль. Попробуйте перезапустить бота командой /start."
        )


@router.callback_query(F.data == "find_customer")
async def handle_find_customer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите номер телефона клиента",
    )
    await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
