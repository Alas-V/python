from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from utils.states import OrderForm
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from queries.orm import OrderQueries, UserQueries
from text_templates import order_data_structure, text_address_data
from aiogram.fsm.context import FSMContext
from keyboards.kb_order import OrderProcessing
import asyncio

processing = Router()


# @processing.callback_query(F.data == "new_address")
# async def first_msg(callback: CallbackQuery, state: FSMContext):
#     telegram_id = callback.from_user.id
#     total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
#     list_of_books = []
#     for book_data in cart_data:
#         books_inside = (
#             f"\n📖{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽"
#         )
#         list_of_books.append(books_inside)
#     user_balance = await UserQueries.get_user_balance(telegram_id)
#     order_data = await OrderQueries.get_user_address_data(telegram_id)
#     text = await order_data_structure(
#         list_of_books, total_price, order_data, user_balance
#     )
#     await callback.message.edit_text(
#         text, reply_markup=await OrderProcessing.kb_change_details()
#     )
#     await state.update_data(message_id=callback.message.message_id)


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)


@processing.callback_query(F.data == "new_address")
async def new_address(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    address_id = await OrderQueries.add_address_get_id(telegram_id)
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    text = await text_address_data(address_data)
    main_message = await callback.message.edit_text(
        text, reply_markup=await OrderProcessing.kb_change_details(address_id)
    )
    hint_message = await callback.message.answer(
        "👤 *Введите ваше имя:*", parse_mode="Markdown"
    )
    await state.update_data(
        address_id=address_id,
        main_message_id=main_message.message_id,  # ID основного сообщения
        last_hint_id=hint_message.message_id,  # ID последней подсказки
        user_messages=[],  # Для сообщений пользователя
        current_step="name",
    )
    await state.set_state(OrderForm.name)
    await callback.answer()


@processing.callback_query(F.data.startswith("edit_address_"))
async def edit_address(callback: CallbackQuery):
    address_id = callback.data.split("_")[2]
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    text = await text_address_data(address_data)
    await callback.message.edit_text(
        text, reply_markup=await OrderProcessing.kb_change_details(address_id)
    )


@processing.callback_query(F.data == "choose_address")
async def choosing_address(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    address = await OrderQueries.get_address_small(telegram_id)
    await callback.message.edit_text(
        "🚚Выберите адрес доставки:",
        reply_markup=await OrderProcessing.kb_choose_address(address),
    )


@processing.callback_query(F.data.startswith("what_to_change_"))
async def choose_change(callback: CallbackQuery):
    address_id = callback.data.split("_")[3]
    await callback.message.edit_text(
        "✏️Выберите что вы хотите изменить или добавить",
        reply_markup=await OrderProcessing.order_details(address_id),
    )


@processing.callback_query(F.data.startswith("change_"))
async def change_details(callback: CallbackQuery, state: FSMContext):
    column = callback.data.split("_")[1]
    address_id = callback.data.split("_")[2]
    if column == "address":
        await callback.message.edit_text(
            "✏️Выберите что вы хотите изменить или добавить",
            reply_markup=await OrderProcessing.kb_address_change(address_id),
        )


# FMScontext hnd


@processing.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="name",
        data=message.text,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"📝 *Создание адреса:*\n\n{text}",
        reply_markup=await OrderProcessing.kb_change_details(address_id),
        parse_mode="Markdown",
    )
    temp_mess = await message.answer("✅ Данные обновлены", show_alert=False)
    await asyncio.sleep(2)
    await temp_mess.delete()
    new_hint = await message.answer("📞 *Введите телефон:*", parse_mode="Markdown")
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="phone"
    )
    await state.set_state(OrderForm.phone)


# @processing.message(OrderForm.name)
# async def info_name(message: Message, state: FSMContext):
#     telegram_id = message.from_user.id
#     await state.update_data(last_bot_msg_id=message.message_id)
#     await delete_user_message(message)
#     await OrderQueries.update_info(telegram_id, "name", message.text)
#     await state.set_state(OrderForm.phone)
#     await edit_or_send_new(message, "📞 Введите ваш номер телефона", state)


# @processing.message(OrderForm.phone)
# async def info_phone(message: Message, state: FSMContext):
#     telegram_id = message.from_user.id
#     await state.update_data(last_bot_msg_id=message.message_id)
#     await delete_user_message(message)
#     await OrderQueries.update_info(telegram_id, "phone", message.text)
#     await state.set_state(OrderForm.city)
#     await edit_or_send_new(message, "🌎 Введите ваш город", state)
