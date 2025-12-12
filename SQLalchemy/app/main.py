from queries.core import (
    create_tables,
    insert_data_author,
    select_books,
    update_user_name,
    update_username,
)
from queries.orm import BookQueries, AuthorQueries, DBData, UserQueries, SaleQueries
from schemas import AuthorCreate
import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import setup_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

setup_router(dp)


async def main():
    await create_tables()
    await DBData.fake_data()
    await SaleQueries.add_on_sale([1, 7, 15, 17, 20, 27, 30, 37, 40, 47, 51, 57], 0.2)
    await SaleQueries.add_on_sale([2, 12, 22, 32, 42, 52], 0.1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
