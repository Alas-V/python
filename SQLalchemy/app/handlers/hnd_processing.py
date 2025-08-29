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


@processing.callback_query(F.data == "new_address")
async def new_address(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    address_id = await OrderQueries.add_address_get_id(telegram_id)
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    text = await text_address_data(address_data)
    await callback.message.edit_text(
        text, reply_markup=await OrderProcessing.kb_change_details(address_id)
    )


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
