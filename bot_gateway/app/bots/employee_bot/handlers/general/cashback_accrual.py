from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.api_client import CoreApiClient
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.employee_bot.keyboards.cashback_accrual import CashbackAccrualKeyboards
from app.bots.employee_bot.states.general import CashbackAccrualStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.callback_query(F.data == "accrue_cashback")
async def start_accrual(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CashbackAccrualStates.WAITING_FOR_ACCRUAL_AMOUNT)
    await callback.message.edit_text("Введите сумму покупки клиента:")
    await callback.answer()


@router.message(StateFilter(CashbackAccrualStates.WAITING_FOR_ACCRUAL_AMOUNT))
async def process_accrual_amount(
    message: Message, state: FSMContext, api_client: CoreApiClient
):
    try:
        purchase_amount = Decimal(message.text.replace(",", "."))
        await state.update_data(purchase_amount=str(purchase_amount))
        await state.set_state(
            CashbackAccrualStates.WAITING_FOR_ACCRUAL_CASHBACK_CONFIRMATION
        )
        await message.answer(
            text=f"Вы уверены, что хотите начислить кэшбэк за покупку на сумму <b>{purchase_amount} рублей</b>?",
            reply_markup=CashbackAccrualKeyboards.to_confirm_cashback_accrual_keyboard,
        )
        if purchase_amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(
            "Неверный формат. Пожалуйста, введите положительное число (например, 1500 или 99.50)."
        )
        return


@router.callback_query(
    StateFilter(CashbackAccrualStates.WAITING_FOR_ACCRUAL_CASHBACK_CONFIRMATION)
)
async def confirm_cashback_accrual(
    callback: CallbackQuery, state: FSMContext, api_client: CoreApiClient
):

    data = await state.get_data()
    jwt_token = data.get("jwt_token")
    customer = data.get("customer_profile")
    customer_role_id = customer.get("id") if customer else None
    purchase_amount_str = data.get("purchase_amount")
    purchase_amount = Decimal(purchase_amount_str) if purchase_amount_str else None
    await state.set_state(None)

    if not all([jwt_token, customer_role_id]):
        await callback.message.answer(
            "Произошла ошибка сессии, начните поиск заново.",
            reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
        )
        return

    response = await api_client.accrue_cashback(
        jwt_token, customer_role_id, purchase_amount
    )

    if response:
        text = (
            f"✅ Успешно!\n\n"
            f"Сумма покупки: {purchase_amount}\n"
            f"Начислено бонусов: <b>{response['cashback_accrued']}</b>\n"
            f"Новый баланс клиента: <b>{response['balance_after']}</b>"
        )
        await callback.message.answer(
            text, reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard
        )
    else:
        await callback.message.answer(
            "Не удалось начислить бонусы (возможно, сумма покупки слишком мала или акция не сработала).",
            reply_markup=MainMenuKeyboards.back_to_main_menu_keyboard,
        )
