from aiogram import Bot, F, Router, types
from queries.orm import (
    OrderQueries,
    BookQueries,
    UserQueries,
    SaleQueries,
    AdminQueries,
)
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart
from keyboards.kb_user import UserKeyboards
from keyboards.kb_review import KbReview
from text_templates import (
    get_book_details,
    get_book_details_on_sale,
    format_order_details,
    INFOTEXT,
    get_full_review,
    book_for_review,
)
from models import AdminPermission
from aiogram.exceptions import TelegramBadRequest
from utils.states import BookDetailsState, UserSearchBook
from utils.admin_utils import PermissionChecker
from aiogram.fsm.context import FSMContext
import asyncio

user_router = Router()


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            # await asyncio.sleep(0.1)
        except Exception as e:
            if "message to delete not found" not in str(
                e
            ) and "message can't be deleted" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


GENRES = {
    "fantasy": "Фэнтази🚀",
    "horror": "Ужасы👻",
    "sciencefiction": "Научная Фантастика🌌",
    "detective": "Детектив🕵️",
    "classic": "Классическая литература🎭",
    "poetry": "Поэзия✒️",
}


# DEBUG для получения id фото
@user_router.message(F.content_type == "photo")
async def get_photo_id(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.answer(
        f"📸 File ID этого фото:\n"
        f"<code>{file_id}</code>\n\n"
        f"Скопируйте этот ID для использования в вашем коде.",
        parse_mode="HTML",
    )


#


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", [])
    last_hint_id = data.get("last_hint_id")
    photo_message_id = data.get("photo_message_id", [])
    if messages_to_delete:
        await delete_messages(message.bot, message.chat.id, [messages_to_delete])
    if last_hint_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=last_hint_id
            )
        except Exception:
            pass
    await state.clear()
    user_data = {
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "user_first_name": message.from_user.first_name,
    }
    is_admin = await AdminQueries.is_user_admin(int(message.from_user.id))
    user = await UserQueries.get_user_if_exist(user_data)
    text = f"""
📖 Привет {user.user_first_name}, Я — Book Bot *DEMO*, твой персональный помощник в мире книг.  

    ✨ Здесь ты можешь:  
    
    - 🛒 Купить новинки и бестселлеры  
    - 🔍 Найти книги по жанрам  
    - 💰 Получать скидки  

Давай начнем! Выбери действие в меню.
    """
    if photo_message_id:
        bot = message.bot
        await delete_messages(bot, message.chat.id, [photo_message_id])
        await message.answer(text, reply_markup=await UserKeyboards.main_menu(is_admin))
        await state.clear()
        return
    await message.answer(text, reply_markup=await UserKeyboards.main_menu(is_admin))


@user_router.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", [])
    last_hint_id = data.get("last_hint_id")
    photo_message_id = data.get("photo_message_id", [])
    if messages_to_delete:
        await delete_messages(
            callback.message.bot, callback.message.chat.id, [messages_to_delete]
        )
    if last_hint_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception:
            pass
    await state.clear()
    is_admin = await AdminQueries.is_user_admin(int(callback.from_user.id))
    text = """
📚 Главное меню Book Bot *DEMO*. Твой персональный помощник в мире книг.

Выберите раздел:

            🔥 Товары со скидкой

    🛒 Корзина             📚 Каталог
    📦 Заказы               📝 Отзывы
    📨 Поддержка        ℹ️ Информация
"""
    await callback.answer("Возвращение в Меню")
    if photo_message_id:
        bot = callback.message.bot
        await delete_messages(bot, callback.message.chat.id, [photo_message_id])
        await callback.message.answer(
            text, reply_markup=await UserKeyboards.main_menu(is_admin)
        )
        await state.clear()
        return
    await callback.message.edit_text(
        text, reply_markup=await UserKeyboards.main_menu(is_admin)
    )


@user_router.callback_query(F.data == "information")
async def information(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        f"{INFOTEXT}", reply_markup=await UserKeyboards.info_out()
    )


@user_router.callback_query(F.data == "catalog")
async def genre_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data:
        await state.clear()
    await callback.answer("")
    await callback.message.edit_text(
        "Выберите жанр для поиска:", reply_markup=await UserKeyboards.show_genre()
    )


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


@user_router.callback_query(F.data == "my_reviews")
async def check_reviews(callback: CallbackQuery):
    telegram_id = int(callback.from_user.id)
    has_draft = await UserQueries.draft_reviews(telegram_id)
    has_published = await UserQueries.published_check(telegram_id)
    if has_draft or has_published:
        message_text = """Выберите раздел Ваших отзывов для просмотра и редактирования
        - 📝 Черновик отзывов
        - 📢 Опубликованные отзывы """
        keyboard = await KbReview.kb_type_review()
    elif not has_draft and not has_published:
        message_text = """📝 У вас пока нет отзывов.\n\nВы можете оставить отзыв на любую купленную книгу"""
        keyboard = await KbReview.kb_no_review()
    await callback.message.edit_text(
        text=message_text,
        reply_markup=keyboard,
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
    telegram_id = int(callback.from_user.id)
    current_state = await state.get_state()
    data = await state.get_data()
    photo_message_id = data.get("photo_message_id", [])
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
    if photo_message_id:
        bot = callback.message.bot
        await delete_messages(bot, callback.message.chat.id, [photo_message_id])
        if total_price > 1:
            has_address = await OrderQueries.has_address(telegram_id)
            if has_address:
                main_message = await callback.message.answer(
                    f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\n💵 Сумма корзины -  {total_price}₽",
                    reply_markup=await UserKeyboards.in_cart_has_address(telegram_id),
                )
            else:
                main_message = await callback.message.answer(
                    f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\nСумма корзины -  {total_price}₽",
                    reply_markup=await UserKeyboards.in_cart_no_address(telegram_id),
                )
        else:
            main_message = await callback.message.answer(
                f"    🛒Ваша корзина пуста!\n\n💳 Ваш баланс - {user_balance}₽",
                reply_markup=await UserKeyboards.in_empty_cart(),
            )
        await state.update_data(main_message_id=main_message.message_id)
        return
    if total_price > 1:
        has_address = await OrderQueries.has_address(telegram_id)
        if has_address:
            await callback.message.edit_text(
                f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\n💵 Сумма корзины -  {total_price}₽",
                reply_markup=await UserKeyboards.in_cart_has_address(telegram_id),
            )
        else:
            await callback.message.edit_text(
                f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\nСумма корзины -  {total_price}₽",
                reply_markup=await UserKeyboards.in_cart_no_address(telegram_id),
            )
    else:
        await callback.message.edit_text(
            f"    🛒Ваша корзина пуста!\n\n💳 Ваш баланс - {user_balance}₽",
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
async def sale_genre(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_message_id = data.get("photo_message_id", [])
    genres = callback.data.split("_")[1]
    books = await BookQueries.get_sale_genre(genres)
    if not books:
        await callback.answer("Книг этого жанра не найдено")
        return
    genre_in_text = GENRES[genres]
    if photo_message_id:
        bot = callback.message.bot
        await delete_messages(bot, callback.message.chat.id, [photo_message_id])
        main_message = await callback.message.answer(
            f"📚 Книги со скидкой в жанре {genre_in_text}:",
            reply_markup=await UserKeyboards.sale_books_by_genre_keyboard(books),
        )
        await state.update_data(main_message_id=main_message.message_id)
        return
    await callback.answer("")
    main_message = await callback.message.edit_text(
        f"📚 Книги со скидкой в жанре {genre_in_text}:",
        reply_markup=await UserKeyboards.sale_books_by_genre_keyboard(books),
    )
    await state.update_data(main_message_id=main_message.message_id)


@user_router.callback_query(F.data.startswith("genre_"))
async def classic_show_books(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_message_id = data.get("photo_message_id", [])
    genres = callback.data.split("_")[1]
    books = await BookQueries.get_book_by_genre(genres)
    if not books:
        await callback.answer("Книг этого жанра не найдено")
        return
    genre_in_text = GENRES[genres]
    await callback.answer()
    if photo_message_id:
        bot = callback.message.bot
        await delete_messages(bot, callback.message.chat.id, [photo_message_id])
        main_message = await callback.message.answer(
            f"📚 Книги в жанре {genre_in_text}:",
            reply_markup=await UserKeyboards.books_by_genre_keyboard(books),
        )
        await state.update_data(main_message_id=main_message.message_id)
        return
    main_message = await callback.message.edit_text(
        f"📚 Книги в жанре {genre_in_text}:",
        reply_markup=await UserKeyboards.books_by_genre_keyboard(books),
    )
    await state.set_state(BookDetailsState.going_to_book)
    await state.update_data(main_message_id=main_message.message_id)


@user_router.callback_query(F.data.startswith("book_"))
async def book_details(callback: CallbackQuery, state: FSMContext):
    try:
        book_id = int(callback.data.split("_")[1])
        data = await state.get_data()
        telegram_id = int(callback.from_user.id)
        last_hint_id = data.get("last_hint_id", [])
        if last_hint_id:
            bot = callback.message.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        book_data = await BookQueries.get_book_info(book_id)
        if not book_data:
            await callback.answer(
                "Не удалось найти книгу. Повторите попытку позже", show_alert=True
            )
            return
        if book_data.get("book_on_sale"):
            text = await get_book_details_on_sale(book_data)
        else:
            text = await get_book_details(book_data)
        genre_in_text = GENRES.get(book_data["book_genre"], book_data["book_genre"])
        book_cover = await BookQueries.has_cover(book_id)
        admin = await AdminQueries.is_user_admin(telegram_id)
        if admin:
            can_manage_book_data = PermissionChecker.has_permission(
                admin.permissions, AdminPermission.MANAGE_BOOKS
            )
        else:
            can_manage_book_data = False
        main_message_id = data.get("main_message_id", [])
        if main_message_id:
            try:
                bot = callback.message.bot
                await delete_messages(bot, callback.message.chat.id, [main_message_id])
            except Exception:
                pass
        await state.update_data(photo_message_id=None)
        if book_cover:
            try:
                photo_message = await callback.message.answer_photo(
                    photo=book_cover,
                    caption=text,
                    reply_markup=await UserKeyboards.book_details(
                        book_data["book_id"],
                        book_data["book_genre"],
                        book_data["book_on_sale"],
                        genre_in_text,
                        can_manage_book_data,
                    ),
                    parse_mode="HTML",
                )
                await state.update_data(photo_message_id=photo_message.message_id)
                await callback.answer()
                return
            except Exception as e:
                print(f"Ошибка при отправке фото: {e}")
                book_cover = None
        try:
            main_message = await callback.message.edit_text(
                text,
                reply_markup=await UserKeyboards.book_details(
                    book_data["book_id"],
                    book_data["book_genre"],
                    book_data["book_on_sale"],
                    genre_in_text,
                    can_manage_book_data,
                ),
                parse_mode="HTML",
            )
            await state.update_data(main_message_id=main_message.message_id)
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            main_message = await callback.message.answer(
                text,
                reply_markup=await UserKeyboards.book_details(
                    book_data["book_id"],
                    book_data["book_genre"],
                    book_data["book_on_sale"],
                    genre_in_text,
                    can_manage_book_data,
                ),
                parse_mode="HTML",
            )
            await state.update_data(main_message_id=main_message.message_id)
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в book_details: {e}")
        await callback.answer(
            "❌ Произошла ошибка при загрузке данных о книге", show_alert=True
        )


@user_router.callback_query(F.data.startswith("add_to_cart_book_"))
async def add_to_cart_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[4])
    telegram_id = int(callback.from_user.id)
    availability = await BookQueries.check_book_availability(book_id, telegram_id)
    if not availability["available"]:
        await callback.answer(f"❌ {availability['message']}", show_alert=True)
        return
    cart_check = await OrderQueries.check_cart_quantity_limit(
        telegram_id, book_id, quantity_to_add=1
    )
    if not cart_check["can_add"]:
        await callback.answer(
            f"❌ Превышен лимит!\n"
            f"В корзине уже: {cart_check['current_in_cart']} шт.\n"
            f"На складе: {cart_check['available_quantity']} шт.\n"
            f"Можно добавить: {cart_check['max_can_add']} шт.",
            show_alert=True,
        )
        return
    await OrderQueries.add_book_to_cart(telegram_id, book_id)
    total_price, books_in_cart = await OrderQueries.get_cart_total(telegram_id)
    total_books_count = sum(book["quantity"] for book in books_in_cart)
    list_of_books = []
    for book_data in books_in_cart:
        books_inside = f"\n{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽/шт."
        list_of_books.append(books_inside)
    full_text = f"Книга успешно добавлена!\nВ вашей корзине:\n{''.join(list_of_books)}\n\nСумма корзины -  {total_price} ₽"
    if len(full_text) > 200:
        text = f"Книга успешно добавлена!\n📚 Книг в корзине: {total_books_count}\n💰 Сумма: {total_price}₽"
    else:
        text = full_text
    await callback.answer(text, show_alert=True)


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
async def reviews_first(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_message_id = data.get("photo_message_id", [])
    book_id = int(callback.data.split("_")[3])
    try:
        data = await BookQueries.get_book_reviews(book_id)
        book_info = data["book_info"]
        reviews = data["reviews"]
        if not book_info:
            await callback.message.answer("❌ Книга не найдена")
            return
        message_text = await book_for_review(book_info)
        if not reviews:
            message_text += "\n📝 <b>Отзывов пока нет</b>\n\n💡 Будьте первым, кто оставит отзыв об этой книге!"
        else:
            message_text += "\n<b>📖 Отзывы читателей:</b>"
        if photo_message_id:
            bot = callback.message.bot
            await delete_messages(bot, callback.message.chat.id, [photo_message_id])
            main_message = await callback.message.answer(
                text=message_text,
                reply_markup=await UserKeyboards.kb_reviews(book_id, reviews),
                parse_mode="HTML",
            )
            await callback.answer()
            await state.update_data(main_message_id=main_message.message_id)
            return
        main_message = await callback.message.edit_text(
            text=message_text,
            reply_markup=await UserKeyboards.kb_reviews(book_id, reviews),
            parse_mode="HTML",
        )
        await callback.answer()
        await state.update_data(main_message_id=main_message.message_id)
    except Exception as e:
        print(f"Ошибка в reviews_first: {e}")
        await callback.answer(
            "❌ Произошла ошибка при загрузке отзывов", show_alert=True
        )


@user_router.callback_query(F.data.startswith("review_"))
async def full_review(callback: CallbackQuery, state: FSMContext):
    review_id = int(callback.data.split("_")[1])
    book_id = int(callback.data.split("_")[2])
    telegram_id = int(callback.from_user.id)
    review_data = await BookQueries.full_book_review(review_id)
    if review_data["telegram_id"] == telegram_id:
        own_review = True
    else:
        own_review = False
    text = await get_full_review(review_data)
    photo_message = await callback.message.edit_text(
        text=text,
        reply_markup=await UserKeyboards.kb_in_review(own_review, review_id, book_id),
        parse_mode="Markdown",
    )
    await state.update_data(photo_message_id=photo_message.message_id)
    await callback.answer()


@user_router.callback_query(F.data == "search_book")
async def search_book_start(callback: CallbackQuery, state: FSMContext):
    try:
        main_message = await callback.message.edit_text(
            text="🔍 Введите название книги для поиска:",
            reply_markup=await UserKeyboards.back_from_search(),
        )
        await state.set_state(UserSearchBook.waiting_for_book_name)
        await state.update_data(
            chat_id=callback.message.chat.id, main_message_id=main_message.message_id
        )
        await callback.answer()
    except Exception as e:
        print(f"Error search_book_start: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# FSM context


@user_router.message(UserSearchBook.waiting_for_book_name, F.text)
async def user_search_book_handler(message: Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        main_message_id = data.get("main_message_id")
        try:
            await message.delete()
        except Exception:
            pass
        search_query = message.text.strip()
        if "%" in search_query or "_" in search_query:
            error_msg = await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=main_message_id,
                text="❌ Введите корректные данные, для поиска книги по названию.",
                reply_markup=await UserKeyboards.back_from_search(),
            )
            await state.set_state(UserSearchBook.waiting_for_book_name)
            await state.update_data(main_message_id=error_msg.message_id)
        if len(search_query) < 2:
            error_msg = await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=main_message_id,
                text="❌ Введите минимум 2 символа. Отправьте название для поиска еще раз",
                reply_markup=await UserKeyboards.back_from_search(),
            )
            await state.set_state(UserSearchBook.waiting_for_book_name)
            await state.update_data(main_message_id=error_msg.message_id)
            return
        books = await BookQueries.search_books_by_title_for_user(search_query)
        if not books:
            main_message = await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=main_message_id,
                text=f"🔍 По запросу '{search_query}' ничего не найдено.\n\nПопробуйте другой запрос:",
                reply_markup=await UserKeyboards.back_from_search(),
            )
            await state.set_state(UserSearchBook.waiting_for_book_name)
            await state.update_data(main_message_id=main_message.message_id)
            return
        if len(books) == 20:
            results_text = (
                f"🔍 По запросу '{search_query}' найдено 20+ книг:\n\nВыберите книгу:"
            )
        else:
            results_text = f"🔍 По запросу '{search_query}' найдено {len(books)} книг:\n\nВыберите книгу:"
        main_message = await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=main_message_id,
            text=results_text,
            reply_markup=await UserKeyboards.user_search_results_keyboard(books),
        )
        await state.set_state(UserSearchBook.loading_book)
        await state.update_data(main_message_id=main_message.message_id)
        return
    except Exception as e:
        print(f"Error in user_search_book_handler: {e}")
        await message.answer("❌ Ошибка при поиске")
        await state.clear()
