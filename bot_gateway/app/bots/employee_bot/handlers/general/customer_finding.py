from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.customer_bot.text.formatters.general import format_transaction_history
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.states.general import EmployeeActionsStates, OnboardingDialogStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter
from aiogram.filters import Command, CommandStart, StateFilter

from app.bots.employee_bot.keyboards.customer_finding import CustomerFindingKeyboards
from app.bots.employee_bot.text.formatters.general import format_customer_profile_for_employee
from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.message(StateFilter(EmployeeActionsStates.WAITING_FOR_CUSTOMER_PHONE))
async def process_customer_phone_search(message: Message, state: FSMContext, api_client: CoreApiClient):
    """
    Обрабатывает введенный номер телефона, ищет клиента и выводит результат.
    """
    customer_phone = message.text
    data = await state.get_data()
    jwt_token = data.get("jwt_token")

    # Сбрасываем состояние поиска в любом случае
    await state.set_state(None)

    api_client = CoreApiClient()
    customer_profile = await api_client.find_customer(jwt_token, customer_phone)

    if customer_profile:
        profile_text = format_customer_profile_for_employee(customer_profile)
        await message.answer(profile_text, reply_markup=CustomerFindingKeyboards.customer_finding_keyboard)
    else:
        await message.answer(
            f"Клиент с номером телефона <b>{customer_phone}</b> не найден.",
            reply_markup=CustomerFindingKeyboards.customer_not_found_keyboard,
        )
