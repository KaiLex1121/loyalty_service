from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.customer_bot.keyboards.view_profile import ViewProfileKeyboards
from app.bots.customer_bot.states.general import MainDialogStates
from app.bots.customer_bot.text.formatters.general import (
    format_promotions,
    format_transaction_history,
)
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))


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
    await state.clear()
    await state.set_state(MainDialogStates.WAITING_IN_MAIN_MENU)


@router.callback_query(F.data == "show_profile")
async def show_profile(
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


@router.callback_query(F.data == "show_promotions")
async def show_promotions(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    company_id: int,
    api_client: CoreApiClient,
):
    promotions = await api_client.get_active_promotions(company_id)
    promo_messages = format_promotions(promotions)

    for promo_text in promo_messages:
        await callback.message.answer(promo_text)
    await callback.message.answer(
        "Это все действующие акции:",
        reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
    )


@router.callback_query(F.data == "show_privacy_policy")
async def show_privacy_policy(callback: CallbackQuery, bot: Bot):
    await callback.message.edit_text(
        text="Политика конфиденциальности",
        reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
    )
