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
    # author_data = {"author_name": "Dante Alighieri", "author_country": "Italy"}
    # validate_data = AuthorCreate(**author_data)
    # await insert_data_author(validate_data)
    # await AuthorQueries.add_author()
    # await AuthorQueries.add_author()
    # await DBData.add_other_data()
    await DBData.fake_data()
    await SaleQueries.add_on_sale([1, 15, 24, 13, 6, 4, 5, 12], 0.2)
    await SaleQueries.add_on_sale([11, 3, 2, 20, 16, 17], 0.1)
    await dp.start_polling(bot)
    # await select_books()
    # await update_user_name(2, "SUMO")
    # await update_username(2, "Master")
    # await AuthorQueries.get_author(15)
    # await UserQueries.get_user(1)
    # await UserQueries.get_user(15)
    # await UserQueries.update_user(15, "lol")
    # await UserQueries.get_user(15)
    # await AuthorQueries.get_author_with_books(2)
    # await BookQueries.get_book(4)
    # await BookQueries.get_book(15)
    # await BookQueries.get_book(12)
    # await BookQueries.select_avg_book_price()
    # await BookQueries.get_avg_price()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
