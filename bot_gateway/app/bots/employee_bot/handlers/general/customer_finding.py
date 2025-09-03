from typing import Union

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.api_client import CoreApiClient
from app.bots.employee_bot.keyboards.customer_finding import CustomerFindingKeyboards
from app.bots.employee_bot.states.general import CustomerFindingStates
from app.bots.employee_bot.text.formatters.general import (
    format_customer_profile_for_employee,
)
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum
from shared.utils.validators import validate_russian_phone

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.message(StateFilter(CustomerFindingStates.WAITING_FOR_CUSTOMER_PHONE))
@router.callback_query(F.data == "cancel_cashback_accrual")
async def process_customer_profile_search(
    event: Union[Message, CallbackQuery], state: FSMContext, api_client: CoreApiClient
):
    """
    Обрабатывает введенный номер телефона, ищет клиента и выводит результат.
    """
    data = await state.get_data()

    if isinstance(event, CallbackQuery):
        customer_profile = data.get("customer_profile")
    else:
        try:
            normalized_phone = validate_russian_phone(event.text)
        except ValueError as e:
            await event.answer(f"{e}\n\nПожалуйста, попробуйте ввести номер еще раз.")
            return
        jwt_token = data.get("jwt_token")
        customer_profile = await api_client.find_customer(jwt_token, normalized_phone)

    if customer_profile:
        await state.update_data(customer_profile=customer_profile)
        profile_text = format_customer_profile_for_employee(customer_profile)

        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                profile_text,
                reply_markup=CustomerFindingKeyboards.customer_finding_keyboard,
            )
        else:
            await event.answer(
                profile_text,
                reply_markup=CustomerFindingKeyboards.customer_finding_keyboard,
            )
    else:
        text = f"Клиент с номером телефона <b>{normalized_phone}</b> не найден."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                text,
                reply_markup=CustomerFindingKeyboards.customer_not_found_keyboard,
            )
        else:
            await event.answer(
                text,
                reply_markup=CustomerFindingKeyboards.customer_not_found_keyboard,
            )

    await state.set_state(None)
