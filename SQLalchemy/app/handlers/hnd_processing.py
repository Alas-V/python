from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from utils.states import OrderForm
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from queries.orm import OrderQueries, UserQueries

processing = Router()


async def delete_user_message(message: Message):
    try:
        await message.delete()
    except:
        pass


@processing.callback_query(F.data == "processing_cart")
async def first_msg(callback: CallbackQuery):
    telegram_id = callback.from_user.id 
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    list_of_books = []
    for book_data in cart_data:
        books_inside = (
            f"\n{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽"
        )
        list_of_books.append(books_inside)
    user_balance = await UserQueries.get_user_balance(telegram_id)
    order_data = await OrderQueries.get_user_order_data(telegram_id)
    name, phone, city, street, house, apartment, payment_method, comment = oder_data




@processing.callback_query(F.data == "processing_cart")
async def order_info(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    await OrderQueries.check_info_if_exist(telegram_id)
    await state.set_state(OrderForm.name)
    text = 
    await callback.message.edit_text(text,)
    await callback.message.answer("👤 Введите имя получателя")


@processing.message(OrderForm.name)
async def info_name(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    await state.update_data(last_bot_msg_id=message.message_id)
    await delete_user_message(message)
    await OrderQueries.update_info(telegram_id, "name", message.text)
    await state.set_state(OrderForm.phone)
    await edit_or_send_new(message, "📞 Введите ваш номер телефона", state)


@processing.message(OrderForm.phone)
async def info_phone(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    await state.update_data(last_bot_msg_id=message.message_id)
    await delete_user_message(message)
    await OrderQueries.update_info(telegram_id, "phone", message.text)
    await state.set_state(OrderForm.city)
    await edit_or_send_new(message, "🌎 Введите ваш город", state)
