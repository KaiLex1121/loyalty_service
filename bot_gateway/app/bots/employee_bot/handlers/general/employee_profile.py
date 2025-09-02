from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.customer_bot.text.formatters.general import format_transaction_history
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.states.general import OnboardingDialogStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.callback_query(F.data == "logout")
async def handle_logout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Вы вышли из системы.")
    await callback.message.answer(
        "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона.",
        reply_markup=OnboardingKeyboards.share_contact_keyboard,
    )
    await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
