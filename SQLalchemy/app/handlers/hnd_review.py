from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import ReviewState
from queries.orm import BookQueries, ReviewQueries
from text_templates import book_for_review
from keyboards.kb_review import KbReview

review_router = Router()


@review_router.callback_query(F.data.startswith("new_review_"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    book_id = int(callback.data.split("_")[2])
    telegram_id = int(callback.from_user.id)
    data = await BookQueries.get_book_reviews(book_id)
    book_info = data["book_info"]
    book_text = await book_for_review(book_info)
    review_id = await ReviewQueries.new_review(telegram_id, book_id)
    main_message = await callback.message.edit_text(
        text=book_text,
        reply_markup=await KbReview.review_main(book_id, review_id),
        parse_mode="HTML",
    )
    hint_message = await callback.message.answer(
        " Как бы вы оценили книгу (от 1⭐ до 5⭐)",
        reply_markup=await KbReview.rating_book(book_id, review_id),
        parse_mode="HTML",
    )
    await state.update_data(
        review_id=review_id,
        main_message_id=main_message.message_id,
        last_hint_id=hint_message.message_id,
        user_messages=[],
        current_step="rating",
    )
    await state.set_state(ReviewState.rating)
    await callback.answer()


@review_router.callback_query(F.data.startswith("rating_"))
async def after_rating(callback: CallbackQuery, state: FSMContext):
    book_id = int(callback.data.split("_")[1])
    review_id = int(callback.data.split("_")[2])
    stars = int(callback.data.split("_")[3])
    is_finished = await ReviewQueries.add_value_column(
        review_id, "review_rating", stars
    )
