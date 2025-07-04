from aiogram.filters.state import State, StatesGroup


class CheckStates(StatesGroup):
    TEST_STATE = State()


class MainStates(StatesGroup):
    MAIN_DIALOG = State()


class ReminderCreateStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_reminder_type = State()
    waiting_for_custom_interval = State()
    waiting_for_start_time_choice = State()
    waiting_for_start_datetime = State()
    waiting_for_reminder_confirmation = State()


class ReminderEditStates(StatesGroup):
    pass
