from aiogram import Dispatcher
from app.bots.employee_bot.handlers.general import main_menu, onboarding, employee_profile, customer_finding
from app.bots.shared.handlers import test

def setup_employee_bot_handlers(dp: Dispatcher):
    dp.include_router(onboarding.router)
    dp.include_router(main_menu.router)
    dp.include_router(employee_profile.router)
    dp.include_router(customer_finding.router)


    dp.include_router(test.router)  # Include test handlers if needed