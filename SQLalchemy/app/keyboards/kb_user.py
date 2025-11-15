from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from queries.orm import OrderQueries


class UserKeyboards:
    @staticmethod
    async def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔥 Товары со скидкой 🔥", callback_data="sale_menu"
                )
            ],
            [
                InlineKeyboardButton(text="🛒Корзина", callback_data="cart"),
                InlineKeyboardButton(text="📚Каталог", callback_data="catalog"),
            ],
            [
                InlineKeyboardButton(text="📦Мои заказы", callback_data="my_orders"),
                InlineKeyboardButton(text="📝Мои отзывы", callback_data="my_reviews"),
            ],
            [InlineKeyboardButton(text="📨 Поддержка", callback_data="support")],
            [InlineKeyboardButton(text="ℹ️Информация", callback_data="information")],
        ]
        if is_admin:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="👑 Админ-панель", callback_data="admin_menu"
                    )
                ],
            )

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def show_genre() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✒️Поэзия", callback_data="genre_poetry"),
                    InlineKeyboardButton(
                        text="🎭Классическая литература", callback_data="genre_classic"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🕵️Детектив", callback_data="genre_detective"
                    ),
                    InlineKeyboardButton(
                        text="🌌Научная Фантастика",
                        callback_data="genre_sciencefiction",
                    ),
                ],
                [
                    InlineKeyboardButton(text="👻Ужасы", callback_data="genre_horror"),
                    InlineKeyboardButton(
                        text="🚀Фэнтази", callback_data="genre_fantasy"
                    ),
                ],
                [InlineKeyboardButton(text="🔙Меню", callback_data="main_menu")],
            ]
        )

    # same for sale
    @staticmethod
    async def show_genre_on_sale() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✒️Поэзия", callback_data="sale_poetry"),
                    InlineKeyboardButton(
                        text="🎭Классическая литература", callback_data="sale_classic"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🕵️Детектив", callback_data="sale_detective"
                    ),
                    InlineKeyboardButton(
                        text="🌌Научная Фантастика",
                        callback_data="sale_sciencefiction",
                    ),
                ],
                [
                    InlineKeyboardButton(text="👻Ужасы", callback_data="sale_horror"),
                    InlineKeyboardButton(
                        text="🚀Фэнтази", callback_data="sale_fantasy"
                    ),
                ],
                [InlineKeyboardButton(text="🔙Меню", callback_data="main_menu")],
            ]
        )

    @staticmethod
    async def books_by_genre_keyboard(books: list) -> InlineKeyboardMarkup:
        keyboard = []
        for book_id, title, is_on_sale, sale_value, rating in books:
            if not rating:
                button_text = f"{title}"
                if is_on_sale:
                    button_text = f"🔥-{int(100 * sale_value)}％🔥 - {title}"
            else:
                button_text = f"{title} - {round(rating, 2)}⭐"
                if is_on_sale:
                    button_text = f"🔥-{int(100 * sale_value)}％🔥 - {title} - {round(rating, 2)}⭐"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"book_{book_id}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(text="🔙Назад к жанрам", callback_data="catalog"),
                InlineKeyboardButton(text="🔙Главное меню", callback_data="main_menu"),
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def sale_books_by_genre_keyboard(
        books: list[dict],
    ) -> InlineKeyboardMarkup:
        keyboard = []
        for book in books:
            button_text = f"🔥-{int(100 * book['sale_value'])}％🔥 - {book['book_title']} - {round(book['book_rating'], 2)}⭐"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"book_{book['book_id']}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад к скидкам", callback_data="sale_menu"
                ),
                InlineKeyboardButton(text="🔙Главное меню", callback_data="main_menu"),
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def book_details(
        book_id: int,
        book_genre: str,
        is_on_sale: bool,
        genre_in_text: str,
        can_manage_book_data: bool,
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📢Отзывы", callback_data=f"reviews_on_book_{book_id}"
                ),
                InlineKeyboardButton(
                    text="🛒Добавить в корзину",
                    callback_data=f"add_to_cart_book_{book_id}",
                ),
            ]
        ]
        if is_on_sale:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="🔥 Товары со скидкой", callback_data=f"sale_{book_genre}"
                    )
                ],
            )
        keyboard.extend(
            [
                [InlineKeyboardButton(text="🛒Корзина", callback_data="cart")],
                [
                    InlineKeyboardButton(
                        text=f"🔙Все книги жанра {genre_in_text}",
                        callback_data=f"genre_{book_genre}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )
        if can_manage_book_data:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="⚙️ Управление товаром ",
                        callback_data=f"admin_book_settings_{book_id}",
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def in_cart_no_address(telegram_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️Отчистить корзину",
                        callback_data=f"delete_cart_{telegram_id}",
                    ),
                    InlineKeyboardButton(
                        text="📃Перейти к оформлению",
                        callback_data="new_address",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    ),
                ],
            ]
        )

    @staticmethod
    async def in_cart_has_address(telegram_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️Отчистить корзину",
                        callback_data=f"delete_cart_{telegram_id}",
                    ),
                    InlineKeyboardButton(
                        text="📃Перейти к оформлению",
                        callback_data="choose_address",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    ),
                ],
            ]
        )

    @staticmethod
    async def in_empty_cart() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔥 Товары со скидкой", callback_data="sale_menu"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📚Каталог",
                        callback_data="catalog",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    ),
                ],
            ]
        )

    @staticmethod
    async def info_out() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙Главное меню", callback_data="main_menu")]
            ]
        )

    @staticmethod
    async def kb_my_orders(
        telegram_id: int, offset: int = 0, limit: int = 5
    ) -> InlineKeyboardMarkup:
        orders = await OrderQueries.get_user_orders(telegram_id, limit, offset)
        total_orders = await OrderQueries.get_user_orders_count(telegram_id)
        keyboard = []
        for order in orders:
            order_id = order["order_id"]
            status = order["status"]
            price = order["price"]
            date = order["created_date"].strftime("%d.%m.%Y")
            button_text = f"📦 Заказ #{order_id} - {price}₽ - {status} - {date}"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text, callback_data=f"order_detail_{order_id}"
                    )
                ]
            )
        navigation_buttons = []
        if offset > 0:
            navigation_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"orders_prev_{offset - limit}_{limit}",
                )
            )
        if offset + limit < total_orders:
            navigation_buttons.append(
                InlineKeyboardButton(
                    text="Дальше ➡️",
                    callback_data=f"orders_next_{offset + limit}_{limit}",
                )
            )
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        keyboard.append(
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_no_my_orders() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📨 Поддержка", callback_data="support")],
                [
                    InlineKeyboardButton(
                        text="🔙 Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_order_detail(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К списку заказов", callback_data="my_orders"
                    ),
                    InlineKeyboardButton(text="📨 Поддержка", callback_data="support"),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_reviews(book_id, reviews) -> InlineKeyboardMarkup:
        keyboard = []
        if reviews:
            rev_place = 0
            for review in reviews:
                keyboard.insert(
                    rev_place,
                    [
                        InlineKeyboardButton(
                            text=f"⭐ {review['review_rating']} - {review['review_title']}",
                            callback_data=f"review_{review['review_id']}_{book_id}",
                        ),
                    ],
                )
                rev_place += 1
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="📝 Написать отзыв", callback_data=f"new_review_{book_id}"
                )
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data=f"book_{book_id}"),
                InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"),
            ],
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_in_review(
        own_review, review_id, book_id=False
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data=f"reviews_on_book_{book_id}"
                ),
                InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"),
            ],
        ]
        if book_id:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="📚 Вернуться к книге", callback_data=f"book_{book_id}"
                    )
                ],
            )
        if own_review:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="📝Редактировать отзыв",
                        callback_data=f"review_edit_{review_id}",
                    ),
                    InlineKeyboardButton(
                        text="🗑️Удалить отзыв",
                        callback_data=f"reviewsdelete_{review_id}",
                    ),
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
