from aiogram.filters.state import State, StatesGroup


class CheckStates(StatesGroup):
    TEST_STATE = State()


class MainDialogStates(StatesGroup):
    WAITING_IN_MAIN_MENU = State()


class OnboardingDialogStates(StatesGroup):
    WAITING_FOR_THE_NUMBER = State()
    WAITING_FOR_ACCEPTANCE = State()
    WAITING_FOR_OUTLET_SELECTION = State()
