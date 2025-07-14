# handlers/start.py
from aiogram import types, Dispatcher
from aiogram.filters import Command
from keyboards.menus import main_menu

def register(dp: Dispatcher):
    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        await message.answer(
            "👋 Привет. Это бот *Ты не один*.\nЗдесь ты можешь делиться мыслями и читать чужие — абсолютно анонимно.",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )