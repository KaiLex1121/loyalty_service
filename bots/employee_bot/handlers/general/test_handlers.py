from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.database.dao.holder import HolderDAO
from src.states.general import CheckStates

router: Router = Router()


@router.message(Command(commands=["get_all"]))
async def get_all_users(
    message: Message,
    dao: HolderDAO,
):
    all_users = await dao.user.get_all()
    await message.answer(text=f"User:{all_users}")


@router.message(Command(commands=["check_state"]))
async def create_state(
    message: Message,
    state: FSMContext,
):
    await state.set_state(CheckStates.TEST_STATE)
    state = await state.get_state()
    await message.answer(text=f"Current state is {state}")


@router.message(Command(commands=["cancel_check_state"]))
async def cancel_state(
    message: Message,
    state: FSMContext,
):
    await state.clear()
    state = await state.get_state()
    await message.answer(text=f"Current state is {state}")


@router.message()
async def message_echo(message: Message, state: FSMContext):
    state = await state.get_state()
    await message.answer(text=f"Message попал сюда c состоянием {state}")


@router.message()
async def callback_echo(callback: CallbackQuery, state: FSMContext):
    state = await state.get_state()
    await callback.answer(text=f"Callback попал сюда c состоянием {state}")
