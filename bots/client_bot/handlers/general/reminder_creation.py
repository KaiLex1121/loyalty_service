from typing import Union

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.database.dao.holder import HolderDAO
from src.database.models.user import User
from src.dto.reminder import CreateReminderDTO
from src.keyboards.reminder_creation import ReminderCreationKeyboards
from src.services.reminder import ReminderService
from src.services.scheduler import SchedulerService
from src.states.general import ReminderCreateStates
from src.text.formatters.reminder_creation import get_formateed_confirmation_text
from src.utils.datetime_utils import (
    convert_dt_to_russian,
    parse_frequency,
    parse_start_time,
)

router: Router = Router()


@router.callback_query(F.data == "create_reminder")
async def fill_reminder_name(callback: CallbackQuery, state: FSMContext, user: User):
    await state.update_data(
        text=None,
        frequency_type=None,
        custom_frequency=None,
        start_datetime=None,
        user_id=user.db_id,
        tg_user_id=user.tg_id,
    )
    await callback.message.edit_text(
        text="Введите краткий текст напоминания",
        reply_markup=ReminderCreationKeyboards.to_main_menu,
    )
    await state.set_state(ReminderCreateStates.waiting_for_name)


@router.message(StateFilter(ReminderCreateStates.waiting_for_name))
async def choose_reminder_type(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        text="Выберите тип объявления",
        reply_markup=ReminderCreationKeyboards.choose_reminder_type,
    )
    await state.set_state(ReminderCreateStates.waiting_for_reminder_type)


@router.callback_query(
    StateFilter(ReminderCreateStates.waiting_for_reminder_type),
    F.data == "other",
)
async def fill_custom_interval(callback: CallbackQuery, state: FSMContext):
    await state.update_data(frequency_type=callback.data)
    await callback.message.edit_text(
        text="Введите свой интервал в формате «1 год 2 месяца 3 дня 4 часа 5 минут»",
        reply_markup=ReminderCreationKeyboards.to_main_menu,
    )
    await state.set_state(ReminderCreateStates.waiting_for_custom_interval)


@router.message(StateFilter(ReminderCreateStates.waiting_for_custom_interval))
@router.callback_query(
    StateFilter(ReminderCreateStates.waiting_for_reminder_type), F.data != "other"
)
async def choose_reminder_start_time(
    event: Union[Message, CallbackQuery], state: FSMContext
):
    if isinstance(event, Message):
        formated_frequency = parse_frequency(event.text)
        await state.update_data(custom_frequency=formated_frequency)
        await event.answer(
            text="Выберите время начала напоминания",
            reply_markup=ReminderCreationKeyboards.choose_reminder_start_time,
        )
        await state.set_state(ReminderCreateStates.waiting_for_start_time_choice)
    else:
        await state.update_data(frequency_type=event.data)
        await event.message.edit_text(
            text="Выберите время начала напоминания",
            reply_markup=ReminderCreationKeyboards.choose_reminder_start_time,
        )
        await state.set_state(ReminderCreateStates.waiting_for_start_time_choice)


@router.callback_query(
    StateFilter(ReminderCreateStates.waiting_for_start_time_choice),
    F.data == "start_another_time",
)
async def fill_start_datetime(callback: CallbackQuery, state: FSMContext):
    await state.update_data(start_datetime=callback.data)
    await callback.message.edit_text(
        text="Введите дату начала напоминания в формате: «1 января 2000 года 12:00» или «12:00», если хотите, чтобы напоминание началось сегодня",
        reply_markup=ReminderCreationKeyboards.to_main_menu,
    )
    await state.set_state(ReminderCreateStates.waiting_for_start_datetime)


@router.callback_query(
    StateFilter(ReminderCreateStates.waiting_for_start_time_choice),
    F.data == "start_now",
)
@router.message(StateFilter(ReminderCreateStates.waiting_for_start_datetime))
async def confirm_reminder_creation(
    event: Union[Message, CallbackQuery],
    state: FSMContext,
):
    if isinstance(event, Message):
        formated_start_datetime = parse_start_time(event.text)
        await state.update_data(start_datetime=formated_start_datetime)
        data = await state.get_data()
        print(data)
        formatted_data = get_formateed_confirmation_text(data)
        await event.answer(
            text=f"{formatted_data}",
            reply_markup=ReminderCreationKeyboards.confirm_reminder_creation,
        )
    else:
        formated_start_datetime = parse_start_time(event.data)
        await state.update_data(start_datetime=formated_start_datetime)
        data = await state.get_data()
        formatted_data = get_formateed_confirmation_text(data)
        await event.message.edit_text(
            text=f"{formatted_data}",
            reply_markup=ReminderCreationKeyboards.confirm_reminder_creation,
        )
    await state.set_state(ReminderCreateStates.waiting_for_reminder_confirmation)


@router.callback_query(
    StateFilter(ReminderCreateStates.waiting_for_reminder_confirmation)
)
async def show_creation_confirmation(
    callback: CallbackQuery,
    state: FSMContext,
    reminder_service: ReminderService,
    dao: HolderDAO,
    scheduler_service: SchedulerService,
):
    data = await state.get_data()
    dto = CreateReminderDTO.from_dict(data)
    next_run = await reminder_service.create_reminder(
        dto=dto, scheduler_service=scheduler_service, dao=dao
    )
    await callback.message.edit_text(
        text=f"Напоминание создано, следующий запуск: {convert_dt_to_russian(next_run)}",
        reply_markup=ReminderCreationKeyboards.to_main_menu,
    )
