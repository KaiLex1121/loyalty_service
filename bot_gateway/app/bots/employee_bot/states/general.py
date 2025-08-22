from aiogram.filters.state import State, StatesGroup


class MainDialogStates(StatesGroup):
    WAITING_IN_MAIN_MENU = State()


class OnboardingDialogStates(StatesGroup):
    WAITING_FOR_PHONE = State()
    WAITING_FOR_PHONE_CONFIRMATION = State()


class EmployeeAuthStates(StatesGroup):
    AUTHENTICATED_EMPLOYEE = State()