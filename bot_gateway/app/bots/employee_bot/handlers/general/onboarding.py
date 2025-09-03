from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from app.api_client import CoreApiClient
from app.bots.employee_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.states.general import OnboardingDialogStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter

from shared.enums.telegram_bot_enums import BotTypeEnum

router = Router()
router.message.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))
router.callback_query.filter(BotTypeFilter(bot_type=BotTypeEnum.EMPLOYEE))


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, company_name: str):
    data = await state.get_data()
    if data.get("jwt_token"):
        await message.answer(
            f"Вы авторизованы как сотрудник компании «{company_name}».",
            reply_markup=MainMenuKeyboards.main_window_keyboard,
        )
    else:
        await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
        await message.answer(
            f"Здравствуйте! Это бот для сотрудников компании «{company_name}».\n\n"
            "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона.",
            reply_markup=OnboardingKeyboards.share_contact_keyboard,
        )


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE), F.contact)
async def handle_phone(
    message: Message, state: FSMContext, company_id: int, api_client: CoreApiClient
):
    phone_number = message.contact.phone_number
    response = await api_client.request_employee_otp(phone_number, company_id)

    if response:
        await state.update_data(phone_number=phone_number)
        await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION)
        await message.answer(
            f"Отлично! На номер {phone_number} отправлен код подтверждения. Пожалуйста, введите его.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer(
            "Сотрудник с таким номером телефона не найден в этой компании. Пожалуйста, обратитесь к администратору или попробуйте снова.",
            reply_markup=OnboardingKeyboards.share_contact_keyboard,
        )


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE))
async def handle_no_contact(message: Message):
    await message.answer(
        "Пожалуйста, отправьте свой рабочий номер телефона, используя кнопку «Поделиться контактом».",
        reply_markup=OnboardingKeyboards.share_contact_keyboard,
    )


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION))
async def handle_otp(
    message: Message, state: FSMContext, company_id: int, api_client: CoreApiClient
):
    data = await state.get_data()
    phone_number = data.get("phone_number")
    otp_code = message.text

    response = await api_client.verify_employee_otp(phone_number, otp_code, company_id)

    if not response:
        await message.answer("Неверный код. Пожалуйста, попробуйте еще раз.")
        return

    if response.get("access_token"):
        # Сценарий А: Токен получен сразу
        await state.update_data(jwt_token=response["access_token"])
        await state.set_state(None)
        await message.answer(
            "Аутентификация пройдена!",
            reply_markup=MainMenuKeyboards.main_window_keyboard,
        )

    elif response.get("outlets"):
        # Сценарий Б: Нужно выбрать точку
        await state.update_data(outlets=response["outlets"])
        await state.set_state(OnboardingDialogStates.WAITING_FOR_OUTLET_SELECTION)
        keyboard = OnboardingKeyboards.get_outlet_selection_keyboard(
            response["outlets"]
        )
        await message.answer(
            "Почти готово! Выберите торговую точку, в которой вы работаете:",
            reply_markup=keyboard,
        )

    else:
        await message.answer("Произошла ошибка. Пожалуйста, начните заново с /start")
        await state.clear()


# НОВЫЙ ХЕНДЛЕР для обработки нажатия на инлайн-кнопку
@router.callback_query(
    StateFilter(OnboardingDialogStates.WAITING_FOR_OUTLET_SELECTION),
    F.data.startswith("select_outlet:"),
)
async def handle_outlet_selection(
    callback: CallbackQuery,
    state: FSMContext,
    company_id: int,
    api_client: CoreApiClient,
):
    outlet_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    phone_number = data.get("phone_number")
    outlets = data.get("outlets")
    current_outlet = next((o for o in outlets if o.get("id") == outlet_id), None)
    await state.update_data(current_outlet=current_outlet)
    if not phone_number:
        await callback.message.edit_text(
            "Произошла ошибка сессии. Начните заново с /start"
        )
        await state.clear()
        return

    response = await api_client.select_employee_outlet(
        phone_number, outlet_id, company_id
    )

    if response and response.get("access_token"):
        await state.update_data(jwt_token=response["access_token"])
        await state.set_state(None)
        await callback.message.delete()  # Удаляем сообщение с кнопками
        await callback.message.answer(
            "Вход выполнен успешно!",
            reply_markup=MainMenuKeyboards.main_window_keyboard,
        )
    else:
        await callback.message.edit_text("Не удалось войти. Попробуйте снова с /start")
        await state.clear()

    await callback.answer()  # Закрываем "часики" на кнопке
