from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.database.dao.holder import HolderDAO
from src.dto.user import User
from src.keyboards.reminder_management import ReminderManagementKeyboards
from src.keyboards.view_created_reminders import ViewCreatedRemindersKeyboards
from src.services.reminder import ReminderService
from src.services.scheduler import SchedulerService

router: Router = Router()


@router.callback_query(F.data == "show_created_reminders")
async def show_created_reminders(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Выберите нужное действие",
        reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
    )


@router.callback_query(F.data == "show_all_reminders_list")
async def show_all_reminders_list(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    dao: HolderDAO,
):
    all_reminders = await reminder_service.get_all_user_reminders(
        dao=dao, user_id=user.db_id
    )
    if not all_reminders:
        await callback.message.edit_text(
            text="У вас нет созданных напоминаний",
            reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
        )
        return
    for reminder in all_reminders:
        keyboard = (
            ReminderManagementKeyboards.get_reminder_management_keyboard_by_status(
                reminder.id, reminder.is_active
            )
        )
        await callback.message.answer(
            text=reminder.text,
            reply_markup=keyboard,
        )
    await callback.message.answer(
        text="Выберите нужное действие",
        reply_markup=ViewCreatedRemindersKeyboards.show_all_reminders_management,
    )


@router.callback_query(F.data == "show_active_reminders_list")
async def show_active_reminders_list(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    dao: HolderDAO,
):
    all_reminders = await reminder_service.get_active_user_reminders(
        dao=dao, user_id=user.db_id
    )
    if not all_reminders:
        await callback.message.edit_text(
            text="У вас нет активных напоминаний",
            reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
        )
        return
    for reminder in all_reminders:
        keyboard = (
            ReminderManagementKeyboards.get_reminder_management_keyboard_by_status(
                reminder.id, reminder.is_active
            )
        )
        await callback.message.answer(
            text=reminder.text,
            reply_markup=keyboard,
        )
    await callback.message.answer(
        text="Выберите нужное действие",
        reply_markup=ViewCreatedRemindersKeyboards.show_active_reminders_management,
    )


@router.callback_query(F.data == "show_disabled_reminders_list")
async def show_disabled_reminders_list(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    dao: HolderDAO,
):
    all_reminders = await reminder_service.get_disabled_user_reminders(
        dao=dao, user_id=user.db_id
    )
    if not all_reminders:
        await callback.message.edit_text(
            text="У вас нет неактивных напоминаний",
            reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
        )
        return
    for reminder in all_reminders:
        keyboard = (
            ReminderManagementKeyboards.get_reminder_management_keyboard_by_status(
                reminder.id, reminder.is_active
            )
        )
        await callback.message.answer(
            text=reminder.text,
            reply_markup=keyboard,
        )
    await callback.message.answer(
        text="Выберите нужное действие",
        reply_markup=ViewCreatedRemindersKeyboards.show_disabled_reminders_management,
    )


@router.callback_query(F.data == "delete_all_active_reminders")
async def delete_all_active_reminders(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
):
    await reminder_service.delete_all_active_user_reminders(
        dao=dao, user_id=user.db_id, scheduler_service=scheduler_service
    )
    await callback.message.edit_text(
        text="Все активные напоминания удалены",
        reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
    )


@router.callback_query(F.data == "delete_all_disabled_reminders")
async def delete_all_disabled_reminders(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
):
    await reminder_service.delete_all_disabled_user_reminders(
        dao=dao, user_id=user.db_id, scheduler_service=scheduler_service
    )
    await callback.message.edit_text(
        text="Все неактивные напоминания удалены",
        reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
    )


@router.callback_query(F.data == "delete_all_reminders")
async def delete_all_reminders(
    callback: CallbackQuery,
    user: User,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
):
    await reminder_service.delete_all_user_reminders(
        dao=dao, user_id=user.db_id, scheduler_service=scheduler_service
    )
    await callback.message.edit_text(
        text="Все напоминания удалены",
        reply_markup=ViewCreatedRemindersKeyboards.show_created_reminders,
    )


@router.callback_query(F.data == "disable_all_active_reminders")
async def disable_all_reminders(
    message: Message,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
    user: User,
):
    await reminder_service.disable_all_user_reminders(
        scheduler_service, dao, user.db_id
    )
    await message.answer(text="Все напоминания отключены")


@router.callback_query(F.data == "enable_all_disabled_reminders")
async def enable_all_reminders(
    message: Message,
    reminder_service: ReminderService,
    scheduler_service: SchedulerService,
    dao: HolderDAO,
    user: User,
):
    await reminder_service.enable_all_user_reminders(scheduler_service, dao, user.db_id)
    await message.answer(text="Все напоминания включены")
