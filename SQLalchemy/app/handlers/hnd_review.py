from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import ReviewState
from queries.orm import BookQueries, ReviewQueries, UserQueries
from text_templates import book_for_review, get_full_review
from keyboards.kb_review import KbReview
import asyncio

review_router = Router()

hints = {
    "rating": "*Как бы вы оценили книгу* (от 1⭐ до 5⭐)",
    "title": "✏️ *Напишите оглавление отзыва* (100 символов)",
    "body": "📝 *Напишите Ваш отзыв на книгу* (1000 символов)",
}

review_model = {
    "rating": "review_rating",
    "title": "review_title",
    "body": "review_body",
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
    review_id = await ReviewQueries.review_exist(telegram_id, book_id)
    if review_id:
        review_data = await BookQueries.full_book_review(review_id)
        text = await get_full_review(review_data, True)
        main_message = await callback.message.edit_text(
            text=text,
            reply_markup=await KbReview.review_main(book_id, review_id),
            parse_mode="Markdown",
        )
        is_complete = await ReviewQueries.check_review_completion(review_id)
        if not is_complete:
            next_field = await ReviewQueries.review_get_next_empty_field(
                review_id,
            )
        await state.update_data(
            review_id=review_id,
            main_message_id=main_message.message_id,
            book_id=book_id,
        )
        field_to_state = {
            "rating": ReviewState.rating,
            "title": ReviewState.title,
            "body": ReviewState.body,
        }
        await state.set_state(field_to_state[next_field])
        hint = await callback.message.answer(hints[next_field])
        await state.update_data(last_hint_id=hint.message_id)
        return
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
    guided_str = callback.data.split("_")[2]
    guided = guided_str.lower() == "true"
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
    if not guided:
        temp_mess = await callback.message.answer(
            "✅ *Данные обновлены*", parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await temp_mess.delete()
        return
    if not is_finished and guided:
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


@review_router.callback_query(F.data.startswith("publish_review_"))
async def publish_new_review(callback: CallbackQuery, state: FSMContext):
    bot = callback.message.bot
    data = await state.get_data()
    review_id = data["review_id"]
    book_id = data["book_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
    review_id = int(callback.data.split("_")[2])
    await ReviewQueries.add_value_column(review_id, "published", True)
    await delete_messages(bot, callback.message.chat.id, [last_hint_id])
    review_data = await BookQueries.full_book_review(review_id)
    text = "✅Отзыв опубликован!✅"
    text += await get_full_review(review_data, True)
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.after_published(book_id, review_id),
        parse_mode="Markdown",
    )


@review_router.callback_query(F.data == "drafts")
async def drafts(callback: CallbackQuery):
    telegram_id = int(callback.from_user.id)
    has_draft = await UserQueries.draft_reviews(telegram_id)
    if has_draft:
        drafts = await UserQueries.get_user_draft(telegram_id)
        message_text = """✏️ Выберите черновик для редактирования или удаления"""
        keyboard = await KbReview.kb_own_reviews(drafts)
    elif not has_draft:
        message_text = """❌ У вас сейчас нет черновиков"""
        keyboard = await KbReview.kb_no_review()
    await callback.message.edit_text(
        text=message_text,
        reply_markup=keyboard,
    )
    await callback.answer()


@review_router.callback_query(F.data == "published")
async def published(callback: CallbackQuery):
    telegram_id = int(callback.from_user.id)
    has_published = await UserQueries.published_check(telegram_id)
    if has_published:
        published = await UserQueries.get_user_published_reviews(telegram_id)
        message_text = """✏️ Выберите отзыв для редактирования или удаления"""
        keyboard = await KbReview.kb_own_reviews(published)
    elif not has_published:
        message_text = """❌ У вас сейчас нет опубликованных отзывов"""
        keyboard = await KbReview.kb_no_review()
    await callback.message.edit_text(
        text=message_text,
        reply_markup=keyboard,
    )
    await callback.answer()


@review_router.callback_query(F.data.startswith("reviewsdelete_"))
async def review_delete(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        text="Вы уверены, что хотите удалить отзыв?\n\nЭто действие будет невозможно отменить",
        reply_markup=await KbReview.sure_delete(review_id),
    )


@review_router.callback_query(F.data.startswith("reviewssure_delete_"))
async def review_delete_sure(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    telegram_id = int(callback.from_user.id)
    deleted = await ReviewQueries.delete_review_sure(review_id, telegram_id)
    if deleted:
        await callback.message.edit_text(
            text=" 🗑️ Отзыв успешно удален",
            reply_markup=await KbReview.review_after_delete(),
        )
        return
    else:
        await callback.message.edit_text(
            text=" ❌ Произошла ошибка, пожалуйста, повторите позднее ",
            reply_markup=await KbReview.review_after_delete(),
        )
    return


@review_router.callback_query(F.data.startswith("reviewchange_"))
async def edit_review(callback: CallbackQuery, state: FSMContext):
    review_id = int(callback.data.split("_")[1])
    book_id = int(callback.data.split("_")[2])
    bot = callback.message.bot
    data = await state.get_data()
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
    user_messages = data.get("user_messages", [])
    await delete_messages(bot, callback.message.chat.id, [last_hint_id] + user_messages)
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    text += "\nВыберите пункт для изменения: "
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.kb_change(review_id, book_id),
        parse_mode="Markdown",
    )


@review_router.callback_query(F.data.startswith("changereview_"))
async def change_review(callback: CallbackQuery, state: FSMContext):
    field = str(callback.data.split("_")[1])
    review_id = int(callback.data.split("_")[2])
    book_id = int(callback.data.split("_")[3])
    await state.update_data(
        review_id=review_id,
        column=field,
        message_id=callback.message.message_id,
    )
    await state.set_state(ReviewState.editing_field)
    if field == "rating":
        hint = await callback.message.answer(
            " Как бы вы оценили книгу (от 1⭐ до 5⭐)",
            reply_markup=await KbReview.rating_book(book_id, review_id, guided=False),
            parse_mode="Markdown",
        )
    else:
        hint = await callback.message.answer(hints[field])
    await state.update_data(last_hint_id=hint.message_id, user_messages=[])
    await callback.answer()


# FSM context


@review_router.message(ReviewState.editing_field)
async def review_editing_field(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    book_id = data["book_id"]
    review_id = data["review_id"]
    field = data["column"]
    column = review_model[field]
    main_message_id = data["message_id"]
    last_hint_id = data.get("last_hint_id")
    user_messages = data.get("user_messages", [])
    new_value = message.text
    await ReviewQueries.add_value_column(review_id, column, new_value)
    if user_messages is not None:
        user_messages.append(message.message_id)
    if last_hint_id:
        await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    is_finished = await ReviewQueries.check_review_completion(review_id)
    review_data = await BookQueries.full_book_review(review_id)
    text = await get_full_review(review_data, True)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await KbReview.review_main(book_id, review_id, is_finished),
        parse_mode="Markdown",
    )
    temp_msg = await message.answer("✅ Отзыв обновлен")
    await asyncio.sleep(1)
    await temp_msg.delete()
    await state.clear()


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
