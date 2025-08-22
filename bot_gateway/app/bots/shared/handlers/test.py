from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.bots.customer_bot.keyboards.main_menu import MainMenuKeyboards
from app.bots.customer_bot.states.general import MainDialogStates


router = Router()

@router.message()
async def message_echo(message: Message, state: FSMContext):
    the_state = await state.get_state()
    await message.answer(text=f"Message попал сюда c состоянием {the_state}")


@router.message()
async def callback_echo(callback: CallbackQuery, state: FSMContext):
    the_state = await state.get_state()
    await callback.answer(text=f"Callback попал сюда c состоянием {the_state}")
