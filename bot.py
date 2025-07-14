import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers import start, talk, listen, manage, support, fallback
import db

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем хендлеры
start.register(dp)
talk.register(dp)
listen.register(dp)
manage.register(dp)
support.register(dp)
fallback.register(dp)

async def main():
    await db.init_db()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())