from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.api_client import CoreApiClient

router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, company_id: int, company_name: str):
    api_client = CoreApiClient()
    telegram_id = message.from_user.id

    # 1. Проверяем, зарегистрирован ли уже пользователь
    customer_profile = await api_client.get_customer_by_telegram_id(telegram_id, company_id)

    if customer_profile:
        # Сценарий А: Пользователь найден
        await message.answer(f"С возвращением в программу лояльности «{company_name}»!")
        # TODO: Показать главное меню с кнопками "Баланс", "Акции" и т.д.
    else:
        # Сценарий Б: Новый пользователь
        builder = ReplyKeyboardBuilder()
        builder.button(text="📱 Поделиться контактом", request_contact=True)

        await message.answer(
            f"Добро пожаловать в программу лояльности «{company_name}»!\n\n"
            "Для завершения регистрации, пожалуйста, поделитесь вашим номером телефона.",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )

@router.message(F.contact)
async def handle_contact(message: types.Message, company_id: int):
    """
    Хендлер, который срабатывает, когда пользователь делится своим контактом.
    """
    contact = message.contact
    # Убедимся, что пользователь делится своим собственным контактом
    if contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, поделитесь своим собственным контактом.")
        return

    api_client = CoreApiClient()

    try:
        # 2. Регистрируем пользователя через Core API
        await api_client.onboard_customer(
            telegram_id=contact.user_id,
            phone_number=contact.phone_number,
            company_id=company_id,
            full_name=message.from_user.full_name
        )

        # 3. Отправляем подтверждение и убираем кастомную клавиатуру
        await message.answer(
            "Спасибо! Вы успешно зарегистрированы.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # TODO: Показать главное меню

    except Exception as e:
        # Обработка ошибок (например, Core API недоступен)
        await message.answer(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        print(f"Onboarding failed for user {contact.user_id}: {e}")

@router.message()
async def message_echo(message: Message, state: FSMContext):
    state = await state.get_state()
    await message.answer(text=f"Message попал сюда c состоянием {state}")


@router.message()
async def callback_echo(callback: CallbackQuery, state: FSMContext):
    state = await state.get_state()
    await callback.answer(text=f"Callback попал сюда c состоянием {state}")
