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
                    callback_data=f"review_change_{review_id}_{book_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Назад к книге", callback_data=f"book_{book_id}"
                ),
                InlineKeyboardButton(
                    text="❌Удалить отзыв", callback_data=f"review_delete_{review_id}"
                ),
            ],
        ]
        if is_finished:
            keyboard.insert(0, [InlineKeyboardButton("✅Опубликовать отзыв")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def rating_book(book_id: int, review_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐⭐⭐",
                        callback_data=f"rating_{book_id}_{review_id}_5",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐⭐", callback_data=f"rating_{book_id}_{review_id}_4"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐⭐⭐", callback_data=f"rating_{book_id}_{review_id}_3"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐⭐", callback_data=f"rating_{book_id}_{review_id}_2"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐", callback_data=f"rating_{book_id}_{review_id}_1"
                    )
                ],
            ]
        )
