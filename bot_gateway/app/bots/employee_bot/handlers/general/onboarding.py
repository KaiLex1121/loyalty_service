from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from app.api_client import CoreApiClient
from app.bots.employee_bot.keyboards.onboarding import OnboardingKeyboards
from app.bots.employee_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.employee_bot.states.general import OnboardingDialogStates
from app.bots.shared.filters.bot_type_filter import BotTypeFilter
from app.bots.employee_bot.filters.employee_auth import EmployeeAuthFilter
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
            reply_markup=MainMenuKeyboards.main_window_keyboard
        )
    else:
        await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE)
        await message.answer(
            f"Здравствуйте! Это бот для сотрудников компании «{company_name}».\n\n"
            "Для входа, пожалуйста, подтвердите ваш рабочий номер телефона.",
            reply_markup=OnboardingKeyboards.share_contact_keyboard
        )

@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE), F.contact)
async def handle_phone(message: Message, state: FSMContext, company_id: int, api_client: CoreApiClient):
    phone_number = message.contact.phone_number
    print(f"Received phone number: {phone_number}")
    response = await api_client.request_employee_otp(phone_number, company_id)

    if response:
        await state.update_data(phone_number=phone_number)
        await state.set_state(OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION)
        await message.answer(
            f"Отлично! На номер {phone_number} отправлен код подтверждения. Пожалуйста, введите его.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Сотрудник с таким номером телефона не найден в этой компании. Пожалуйста, обратитесь к администратору или попробуйте снова.",
            reply_markup=OnboardingKeyboards.share_contact_keyboard
        )


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE))
async def handle_phone(message: Message):
    await message.answer(
        "Пожалуйста, отправьте свой рабочий номер телефона, используя кнопку «Поделиться контактом».",
        reply_markup=OnboardingKeyboards.share_contact_keyboard
    )


@router.message(StateFilter(OnboardingDialogStates.WAITING_FOR_PHONE_CONFIRMATION))
async def handle_otp(message: Message, state: FSMContext, company_id: int, company_name: str, api_client: CoreApiClient):
    data = await state.get_data()
    phone_number = data.get("phone_number")
    otp_code = message.text

    if not phone_number:
        await message.answer("Произошла ошибка. Пожалуйста, начните заново с /start")
        await state.clear()
        return

    response = await api_client.verify_employee_otp(phone_number, otp_code, company_id)

    if response and response.get("access_token"):
        await state.update_data(jwt_token=response["access_token"])
        await state.update_data(is_authenticated=True)
        await message.answer(
            f"Аутентификация пройдена успешно! Добро пожаловать.",
            reply_markup=MainMenuKeyboards.main_window_keyboard
        )

    else:
        await message.answer("Неверный код. Пожалуйста, попробуйте еще раз.")
