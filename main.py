
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from bot.router import setup_routers


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    setup_routers(dp)

    print("SUPERQUEST BOT запущен!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
