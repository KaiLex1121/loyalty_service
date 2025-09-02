from aiogram.filters.state import State, StatesGroup


class MainDialogStates(StatesGroup):
    WAITING_IN_MAIN_MENU = State()


class OnboardingDialogStates(StatesGroup):
    WAITING_FOR_PHONE = State()
    WAITING_FOR_PHONE_CONFIRMATION = State()
    WAITING_FOR_OUTLET_SELECTION = State()


class EmployeeActionsStates(StatesGroup): # <-- НОВАЯ ГРУППА СОСТОЯНИЙ
    WAITING_FOR_CUSTOMER_PHONE = State()
    WAITING_FOR_ACCRUAL_AMOUNT = State()
    WAITING_FOR_SPENDING_AMOUNT = State()