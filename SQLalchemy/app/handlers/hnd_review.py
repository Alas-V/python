from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import ReviewState
from queries.orm import BookQueries, ReviewQueries
from text_templates import book_for_review, get_full_review
from keyboards.kb_review import KbReview
import asyncio

review_router = Router()

hints = {
    "rating": "*Как бы вы оценили книгу* (от 1⭐ до 5⭐)",
    "title": "✏️ *Напишите оглавление отзыва* (100 символов)",
    "body": "📝 *Напишите Ваш отзыв на книгу* (1000 символов)",
}


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


@review_router.callback_query(F.data.startswith("new_review_"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    book_id = int(callback.data.split("_")[2])
    telegram_id = int(callback.from_user.id)
    review_id = await ReviewQueries.new_review(telegram_id, book_id)
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    main_message = await callback.message.edit_text(
        text=text,
        reply_markup=await KbReview.review_main(book_id, review_id),
        parse_mode="Markdown",
    )
    hint_message = await callback.message.answer(
        " Как бы вы оценили книгу (от 1⭐ до 5⭐)",
        reply_markup=await KbReview.rating_book(book_id, review_id),
        parse_mode="Markdown",
    )
    await state.update_data(
        review_id=review_id,
        main_message_id=main_message.message_id,
        last_hint_id=hint_message.message_id,
        user_messages=[],
        book_id=book_id,
        current_step="rating",
    )
    await state.set_state(ReviewState.rating)
    await callback.answer()


@review_router.callback_query(F.data.startswith("rating_"))
async def after_rating(callback: CallbackQuery, state: FSMContext):
    bot = callback.message.bot
    data = await state.get_data()
    review_id = data["review_id"]
    book_id = data["book_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
    stars = int(callback.data.split("_")[1])
    is_finished = await ReviewQueries.add_value_column(
        review_id, "review_rating", stars
    )
    await delete_messages(bot, callback.message.chat.id, [last_hint_id])
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.review_main(book_id, review_id, is_finished),
        parse_mode="Markdown",
    )
    if not is_finished:
        temp_mess = await callback.message.answer(
            "✅ *Данные обновлены*", parse_mode="Markdown"
        )
        next_field = await ReviewQueries.review_get_next_empty_field(review_id)
        hint_mgs = hints[f"{next_field}"]
        if next_field == "rating":
            new_hint = await callback.message.answer(
                text=hint_mgs,
                reply_markup=await KbReview.rating_book(book_id, review_id),
                parse_mode="Markdown",
            )
            await state.set_state(getattr(ReviewState, next_field))
        else:
            new_hint = await callback.message.answer(
                text=hint_mgs, parse_mode="Markdown"
            )
            await state.set_state(getattr(ReviewState, next_field))
        await asyncio.sleep(1)
        await temp_mess.delete()
        await state.update_data(
            last_hint_id=new_hint.message_id,
            user_messages=[],
            current_step=f"{next_field}",
        )
    if is_finished:
        temp_mess = await callback.message.answer(
            "✅ *Отзыв заполнен и готов к публикации*", parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await temp_mess.delete()


# FSM context


@review_router.message(ReviewState.title)
async def new_title(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    review_id = data["review_id"]
    book_id = data["book_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    title = message.text.strip().lower().capitalize()
    is_finished = await ReviewQueries.add_value_column(review_id, "review_title", title)
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.review_main(book_id, review_id, is_finished),
        parse_mode="Markdown",
    )
    if not is_finished:
        temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
        next_field = await ReviewQueries.review_get_next_empty_field(review_id)
        hint_mgs = hints[f"{next_field}"]
        if next_field == "rating":
            new_hint = await message.answer(
                text=hint_mgs,
                reply_markup=await KbReview.rating_book(book_id, review_id),
                parse_mode="Markdown",
            )
            await state.set_state(getattr(ReviewState, next_field))
        else:
            new_hint = await message.answer(text=hint_mgs, parse_mode="Markdown")
            await state.set_state(getattr(ReviewState, next_field))
        await asyncio.sleep(1)
        await temp_mess.delete()
        await state.update_data(
            last_hint_id=new_hint.message_id,
            user_messages=[],
            current_step=f"{next_field}",
        )
    if is_finished:
        temp_mess = await message.answer(
            "✅ *Отзыв заполнен и готов к публикации*", parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await temp_mess.delete()


@review_router.message(ReviewState.body)
async def new_body(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    review_id = data["review_id"]
    book_id = data["book_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    body = message.text.strip().lower().capitalize()
    is_finished = await ReviewQueries.add_value_column(review_id, "review_body", body)
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.review_main(book_id, review_id, is_finished),
        parse_mode="Markdown",
    )
    if not is_finished:
        temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
        next_field = await ReviewQueries.review_get_next_empty_field(review_id)
        hint_mgs = hints[f"{next_field}"]
        if next_field == "rating":
            new_hint = await message.answer(
                text=hint_mgs,
                reply_markup=await KbReview.rating_book(book_id, review_id),
                parse_mode="Markdown",
            )
            await state.set_state(getattr(ReviewState, next_field))
        else:
            new_hint = await message.answer(text=hint_mgs, parse_mode="Markdown")
            await state.set_state(getattr(ReviewState, next_field))
        await asyncio.sleep(1)
        await temp_mess.delete()
        await state.update_data(
            last_hint_id=new_hint.message_id,
            user_messages=[],
            current_step=f"{next_field}",
        )
    if is_finished:
        temp_mess = await message.answer(
            "✅ *Отзыв заполнен и готов к публикации*", parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await temp_mess.delete()
