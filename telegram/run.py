import asyncio

from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import setup_router


bot = Bot(token=TOKEN)
dp = Dispatcher()


setup_router(dp)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
