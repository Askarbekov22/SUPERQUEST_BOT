
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from bot.router import setup_routers
from bot.database.storage import init_db


async def main():

    logging.basicConfig(
        level=logging.INFO
    )

    # Инициализация базы данных
    await init_db()

    bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher()

    # Подключаем все направления
    setup_routers(dp)

    print("SUPERQUEST BOT запущен!")
    print("База данных подключена!")

    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
