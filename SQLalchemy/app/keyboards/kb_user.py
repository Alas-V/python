from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class UserKeyboards:
    @staticmethod
    async def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📦Мои заказы", callback_data="confirmed_orders"
                    )
                ],
                [
                    InlineKeyboardButton(text="🛒Корзина", callback_data="cart"),
                    InlineKeyboardButton(text="📚Каталог", callback_data="catalog"),
                ],
                [
                    InlineKeyboardButton(
                        text="🔥 Товары со скидкой", callback_data="sale_menu"
                    )
                ],
                [InlineKeyboardButton(text="📨 Поддержка", callback_data="support")],
                [InlineKeyboardButton(text="ℹ️Информация", callback_data="information")],
            ]
        )

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
                        callback_data="genre_science_fiction",
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
                        callback_data="sale_science_fiction",
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
                InlineKeyboardButton(text="🔙 Назад к жанрам", callback_data="catalog"),
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
        book_id: int, book_genre: str, is_on_sale: bool, genre_in_text: str
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
                [
                    InlineKeyboardButton(
                        text=f"🔙Все книги жанра {genre_in_text}",
                        callback_data=f"genre_{book_genre}",
                    )
                ],
                [InlineKeyboardButton(text="🛒Корзина", callback_data="cart")],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    )
                ],
            ]
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
