from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.customer_bot.text.formatters.general import format_transaction_history
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.CUSTOMER))


@router.callback_query(F.data == "show_balance")
async def show_balance(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    company_id: int,
    api_client: CoreApiClient,
):
    profile = await api_client.get_customer_profile(callback.from_user.id, company_id)
    if profile:
        await callback.message.edit_text(
            f"Ваш текущий баланс: <b>{profile['cashback_balance']}</b> баллов.",
            reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
        )
    else:
        await callback.message.edit_text(
            "Не удалось получить ваш профиль. Попробуйте перезапустить бота командой /start.",
            reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
        )


@router.callback_query(F.data == "show_operations")
async def show_transaction_history(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    company_id: int,
    api_client: CoreApiClient,
):
    profile = await api_client.get_customer_profile(callback.from_user.id, company_id)
    if not profile:
        await callback.message.edit_text(
            "Не удалось получить ваш профиль. Попробуйте перезапустить бота командой /start."
        )
        return
    transactions = await api_client.get_transaction_history(profile["id"])
    history_text = format_transaction_history(transactions)
    await callback.message.edit_text(
        history_text, reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard
    )
