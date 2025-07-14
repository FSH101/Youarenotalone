# main.py
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import start, talk, listen, manage, support, fallback
import db

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем все хендлеры
def register_handlers():
    start.register(dp)
    talk.register(dp)
    listen.register(dp)
    manage.register(dp)
    support.register(dp)
    fallback.register(dp)

async def main():
    await db.init_db()
    register_handlers()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())