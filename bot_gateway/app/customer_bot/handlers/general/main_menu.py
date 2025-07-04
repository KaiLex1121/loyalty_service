from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, company_name: str):
    await message.answer(f"Добро пожаловать в программу лояльности «{company_name}»!")