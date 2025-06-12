from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.filters import admin

router: Router = Router()
router.message.filter(admin.AdminFilter())


async def message_echo(message: Message, state: FSMContext):
    state = await state.get_state()
    await message.answer(text=f"Message попал сюда c состоянием {state}")


async def callback_echo(callback: CallbackQuery, state: FSMContext):
    state = await state.get_state()
    await callback.answer(text=f"Callback попал сюда c состоянием {state}")
