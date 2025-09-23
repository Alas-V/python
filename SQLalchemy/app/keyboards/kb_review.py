from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class KbReview:
    @staticmethod
    async def review_main(
        book_id: int, review_id, is_finished=False
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="➕  Изменить отзыв",
                    callback_data=f"reviewchange_{review_id}_{book_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Назад к книге", callback_data=f"book_{book_id}"
                ),
                InlineKeyboardButton(
                    text="🗑️ Удалить отзыв", callback_data=f"reviewsdelete_{review_id}"
                ),
            ],
        ]
        if is_finished:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="✅Опубликовать отзыв",
                        callback_data=f"publish_review_{review_id}",
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def rating_book(
        book_id: int, review_id, guided: bool = True
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐⭐⭐",
                        callback_data=f"rating_5_{guided}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐⭐", callback_data=f"rating_4_{guided}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐", callback_data=f"rating_3_{guided}"
                    )
                ],
                [InlineKeyboardButton(text="⭐⭐", callback_data=f"rating_2_{guided}")],
                [InlineKeyboardButton(text="⭐", callback_data=f"rating_1_{guided}")],
            ]
        )

    @staticmethod
    async def after_published(book_id: int, review_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝Открыть отзыв",
                        callback_data=f"review_{review_id}_{book_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_type_review() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝Черновики", callback_data="drafts")],
                [
                    InlineKeyboardButton(
                        text="📢Опубликованные", callback_data="published"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="account")],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_no_review() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚Каталог", callback_data="catalog")],
                [
                    InlineKeyboardButton(text="🔙 Назад", callback_data="account"),
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    ),
                ],
            ]
        )

    @staticmethod
    async def kb_own_reviews(reviews) -> InlineKeyboardMarkup:
        keyboard = []
        rev_place = 0
        for review in reviews:
            stars = review.get("review_rating", False)
            if stars:
                keyboard.insert(
                    rev_place,
                    [
                        InlineKeyboardButton(
                            text=f"📖 {review['book_title']} - {stars} ⭐",
                            callback_data=f"review_{review['review_id']}_{review['book_id']}",
                        ),
                    ],
                )
            else:
                keyboard.insert(
                    rev_place,
                    [
                        InlineKeyboardButton(
                            text=f"📖 {review['book_title']}",
                            callback_data=f"review_{review['review_id']}_{review['book_id']}",
                        ),
                    ],
                )
            rev_place += 1
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def review_after_delete() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚Каталог", callback_data="catalog")],
                [InlineKeyboardButton(text="📝Мои отзывы", callback_data="my_reviews")],
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="main_menu"
                    )
                ],
            ]
        )

    @staticmethod
    async def sure_delete(review_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить",
                        callback_data=f"reviewssure_delete_{review_id}",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="my_reviews")],
            ]
        )

    @staticmethod
    async def kb_change(
        review_id: int, book_id: int, is_finished: bool = False
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="⭐ Оценка отзыва",
                    callback_data=f"changereview_rating_{review_id}_{book_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Заголовок",
                    callback_data=f"changereview_title_{review_id}_{book_id}",
                ),
                InlineKeyboardButton(
                    text="📝 Текст",
                    callback_data=f"changereview_body_{review_id}_{book_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data=f"new_review_{book_id}"
                )
            ],
        ]
        if is_finished:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="✅Опубликовать отзыв",
                        callback_data=f"publish_review_{review_id}",
                    )
                ],
            )

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
