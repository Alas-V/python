from aiogram import F, Router
from queries.orm import OrderQueries, BookQueries, UserQueries, SaleQueries
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart
from keyboards.kb_user import UserKeyboards
from text_templates import (
    get_book_details,
    get_book_details_on_sale,
    format_order_details,
    INFOTEXT,
    get_full_review,
)
from aiogram.fsm.context import FSMContext

user_router = Router()


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)


GENRES = {
    "fantasy": "Фэнтази🚀",
    "horror": "Ужасы👻",
    "science_fiction": "Научная Фантастика🌌",
    "detective": "Детектив🕵️",
    "classic": "Классическая литература🎭",
    "poetry": "Поэзия✒️",
}


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data["last_hint_id"]
        if last_hint_id:
            bot = message.bot
            await delete_messages(bot, message.chat.id, [last_hint_id])
        await state.clear()
    user_data = {
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "user_first_name": message.from_user.first_name,
    }
    user = await UserQueries.get_user_if_exist(user_data)
    text = f"""
📖 Привет {user.user_first_name}, Я — Book Bot *DEMO*, твой персональный помощник в мире книг.  

    ✨ Здесь ты можешь:  
    
    - 🛒 Купить новинки и бестселлеры  
    - 🔍 Найти книги по жанрам  
    - 💰 Получать скидки  

Давай начнем! Выбери действие в меню.
    """
    await message.answer(text, reply_markup=await UserKeyboards.main_menu())


@user_router.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery):
    text = """
        📚 Главное меню Book Bot  

Выберите раздел:  

    - 🛒 Корзина 
    - 📚 Каталог       
    - 🔥 Товары со скидкой  
    - ℹ️ Информация 
    """
    await callback.answer("Возвращение в Меню")
    await callback.message.edit_text(text, reply_markup=await UserKeyboards.main_menu())


@user_router.callback_query(F.data == "information")
async def information(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        f"{INFOTEXT}", reply_markup=await UserKeyboards.info_out()
    )


@user_router.callback_query(F.data == "catalog")
async def genre_search(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "Выберите жанр для поиска:", reply_markup=await UserKeyboards.show_genre()
    )


# TODO
@user_router.callback_query(F.data == "my_orders")
async def check_my_orders(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    orders_count = await OrderQueries.get_user_orders_count(telegram_id)
    if orders_count == 0:
        await callback.message.edit_text(
            "📦 У вас пока нет заказов",
            reply_markup=await UserKeyboards.kb_no_my_orders(),
        )
        return
    await callback.message.edit_text(
        f"📦 Ваши заказы ({orders_count} шт.):",
        reply_markup=await UserKeyboards.kb_my_orders(telegram_id),
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("orders_"))
async def orders_pagination(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    if callback.data.startswith("orders_prev_"):
        parts = callback.data.split("_")
        offset = int(parts[2])
        limit = int(parts[3])
    elif callback.data.startswith("orders_next_"):
        parts = callback.data.split("_")
        offset = int(parts[2])
        limit = int(parts[3])
    await callback.message.edit_text(
        "📦 Ваши заказы:",
        reply_markup=await UserKeyboards.kb_my_orders(telegram_id, offset, limit),
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("order_detail_"))
async def order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    order_details = await OrderQueries.get_order_details(order_id, telegram_id)
    if not order_details:
        await callback.answer("Заказ не найден")
        return
    text = await format_order_details(order_details)
    await callback.message.edit_text(
        text,
        reply_markup=await UserKeyboards.kb_order_detail(order_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@user_router.callback_query(F.data == "cart")
async def cart(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    list_of_books = []
    for book_data in cart_data:
        books_inside = (
            f"\n📖{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽"
        )
        list_of_books.append(books_inside)
    user_balance = await UserQueries.get_user_balance(telegram_id)
    await callback.answer("Корзина")
    if total_price > 1:
        has_address = await OrderQueries.has_address(telegram_id)
        if has_address:
            await callback.message.edit_text(
                f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\n💵 Сумма корзины -  {total_price}₽",
                reply_markup=await UserKeyboards.in_cart_has_address(telegram_id),
            )
        else:
            await callback.message.edit_text(
                f"    🛒Корзина\n📖{''.join(list_of_books)}\n\nВаш баланс - {user_balance}₽\nСумма корзины -  {total_price}₽",
                reply_markup=await UserKeyboards.in_cart_no_address(telegram_id),
            )
    else:
        await callback.message.edit_text(
            f"    🛒Ваша корзина пуста!\n\nВаш баланс - {user_balance}₽",
            reply_markup=await UserKeyboards.in_empty_cart(),
        )


@user_router.callback_query(F.data == "sale_menu")
async def sale_menu(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "🔥 Книги со скидками 🔥\nВыберите жанр для поиска:",
        reply_markup=await UserKeyboards.show_genre_on_sale(),
    )


@user_router.callback_query(F.data.startswith("sale_"))
async def sale_genre(callback: CallbackQuery):
    genres = callback.data.split("_")[1]
    books = await SaleQueries.get_sale_genre(genres)
    if not books:
        await callback.answer("Книг этого жанра не найдено")
        return
    genre_in_text = GENRES[genres]
    await callback.answer("")
    await callback.message.edit_text(
        f"📚 Книги со скидкой в жанре {genre_in_text}:",
        reply_markup=await UserKeyboards.sale_books_by_genre_keyboard(books),
    )


@user_router.callback_query(F.data.startswith("genre_"))
async def classic_show_books(callback: CallbackQuery):
    genres = callback.data.split("_")[1]
    books = await BookQueries.get_book_by_genre(genres)
    if not books:
        await callback.answer("Книг этого жанра не найдено")
        return
    genre_in_text = GENRES[genres]
    await callback.answer()
    await callback.message.edit_text(
        f"📚 Книги в жанре {genre_in_text}:",
        reply_markup=await UserKeyboards.books_by_genre_keyboard(books),
    )


@user_router.callback_query(F.data.startswith("book_"))
async def book_details(callback: CallbackQuery):
    book_id = callback.data.split("_")[1]
    book_data = await BookQueries.get_book_info(book_id)
    if not book_data:
        await callback.answer(
            "Не удалось найти книгу. Повторите попытку позже", show_alert=True
        )
        return
    if book_data["book_on_sale"]:
        text = await get_book_details_on_sale(book_data)
    else:
        text = await get_book_details(book_data)
    genre_in_text = GENRES[book_data["book_genre"]]
    await callback.message.edit_text(
        text,
        reply_markup=await UserKeyboards.book_details(
            book_data["book_id"],
            book_data["book_genre"],
            book_data["book_on_sale"],
            genre_in_text,
        ),
        parse_mode="HTML",
    )


@user_router.callback_query(F.data.startswith("add_to_cart_book_"))
async def add_to_cart_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[4])
    telegram_id = callback.from_user.id
    await OrderQueries.add_book_to_cart(telegram_id, book_id)
    total_price, books_in_cart = await OrderQueries.get_cart_total(telegram_id)
    list_of_books = []
    for book_data in books_in_cart:
        books_inside = f"\n{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽/шт."
        list_of_books.append(books_inside)
    await callback.answer(
        f"Книга успешно добавлена!\nВ вашей корзине:\n{''.join(list_of_books)}\n\nСумма корзины -  {total_price} ₽",
        show_alert=True,
    )


@user_router.callback_query(F.data.startswith("delete_cart_"))
async def clean_the_cart(callback: CallbackQuery):
    telegram_id = int(callback.data.split("_")[2])
    del_cart, telegram_id = await OrderQueries.del_cart(telegram_id)
    if del_cart:
        await callback.answer("Ваша корзина отчищена!", show_alert=True)
    else:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
    user_balance = await UserQueries.get_user_balance(telegram_id)
    await callback.message.edit_text(
        f"    🛒Ваша корзина пуста!\n\nВаш баланс - {user_balance}₽",
        reply_markup=await UserKeyboards.in_empty_cart(),
    )


@user_router.callback_query(F.data.startswith("reviews_on_book_"))
async def reviews_first(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[3])
    data = await BookQueries.get_book_reviews(book_id)
    book_info = data["book_info"]
    reviews = data["reviews"]
    if not book_info:
        await callback.message.answer("Книга не найдена")
        return
    message_text = (
        f"📖 <b>{book_info['book_title']}</b>\n"
        f"👤 Автор: {book_info['author_name'] or 'Неизвестен'}\n"
        f"⭐ Средняя оценка: {book_info['avg_rating'] or 0:.1f}/5\n"
        f"💬 Количество отзывов: {book_info['reviews_count'] or 0}\n\n"
        f"<b>Отзывы:</b>"
    )
    await callback.message.edit_text(
        text=message_text,
        reply_markup=await UserKeyboards.kb_reviews(book_id, reviews),
        parse_mode="HTML",
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("review_"))
async def full_review(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[1])
    book_id = int(callback.data.split("_")[2])
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data)
    await callback.message.edit_text(
        text=text,
        reply_markup=await UserKeyboards.kb_in_review(book_id),
        parse_mode="Markdown",
    )
