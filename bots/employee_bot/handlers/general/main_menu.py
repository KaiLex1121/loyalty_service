from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.database.dao.holder import HolderDAO
from src.dto.user import User
from src.keyboards.main_menu import MainMenuKeyboards
from src.services.reminder import ReminderService
from src.services.scheduler import SchedulerService
from src.states.general import MainStates

router: Router = Router()


@router.callback_query(F.data == "to_main_menu")
async def render_main_menu(callback: CallbackQuery, bot: Bot, state: FSMContext):
    text = "Вы вернулись в главное меню.\nВыберите действие"
    try:
        await callback.message.edit_text(
            text=text, reply_markup=MainMenuKeyboards.main_window
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text=text, reply_markup=MainMenuKeyboards.main_window
        )
    await state.clear()
    await state.set_state(MainStates.MAIN_DIALOG)


@router.message(Command("start"))
async def get_started(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    await message.answer(
        text="Выберите действие", reply_markup=MainMenuKeyboards.main_window
    )
    await state.set_state(MainStates.MAIN_DIALOG)


@router.message(Command("create_reminder"))
async def create_reminder(
    message: Message,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
    user: User,
):
    await reminder_service.create_new_reminder(
        scheduler_service=scheduler_service,
        dao=dao,
        user_id=user.db_id,
        tg_user_id=user.tg_id,
        text="Test",
        start_datetime=datetime.now(),
        frequency_type="DAILY",
        custom_frequency={
            "day": 1,
            "hour": 0,
            "minute": 0,
        },
    )

    await message.answer(text="Yo")


@router.message(Command("disable_reminders"))
async def disable_reminders(
    message: Message,
    scheduler_service: SchedulerService,
):
    await scheduler_service.remove_all_jobs()
    await message.answer(text="Removed")
