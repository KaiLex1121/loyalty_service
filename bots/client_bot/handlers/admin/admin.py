from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.redis import Redis
from aiogram.types import CallbackQuery, ContentType, Message
from src.database.dao.holder import HolderDAO
from src.filters import admin
from src.services.broadcaster import broadcast
from src.states.admin import MakeBroadcastState

router: Router = Router()
router.message.filter(admin.AdminFilter())


async def message_echo(message: Message, state: FSMContext):
    state = await state.get_state()
    await message.answer(text=f"Message попал сюда c состоянием {state}")


async def callback_echo(callback: CallbackQuery, state: FSMContext):
    state = await state.get_state()
    await callback.answer(text=f"Callback попал сюда c состоянием {state}")
