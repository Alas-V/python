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
        text,
        reply_markup=await OrderProcessing.kb_change_details(
            address_id, is_complete=False
        ),
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


@processing.callback_query(F.data == "skip_state")
async def skip_state(callback: CallbackQuery, state: FSMContext):
    temp_mess = await callback.message.answer(
        "✅ *Данные обновлены*", parse_mode="Markdown"
    )
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data["last_hint_id"]
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    await asyncio.sleep(1.3)
    await temp_mess.delete()


@processing.callback_query(F.data.startswith("edit_address_"))
async def edit_address(callback: CallbackQuery):
    address_id_str = callback.data.split("_")[2]
    address_id = int(address_id_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    text = await text_address_data(address_data)
    is_complete = await OrderQueries.check_address_completion(address_id)
    await callback.message.edit_text(
        text,
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )


@processing.callback_query(F.data == "choose_address")
async def choose_address(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    addresses = await OrderQueries.get_address_small(telegram_id)
    await callback.message.edit_text(
        "🚚Выберите адрес доставки:",
        reply_markup=await OrderProcessing.kb_choose_address(addresses),
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
    formatted_name = message.text.strip().lower().capitalize()
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="name",
        data=formatted_name,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
        parse_mode="Markdown",
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    new_hint = await message.answer("📞 *Введите телефон:*", parse_mode="Markdown")
    await state.set_state(OrderForm.phone)
    await asyncio.sleep(1.3)
    await temp_mess.delete()
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="phone"
    )


@processing.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="phone",
        data=message.text,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text_address = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    new_hint = await message.answer("🗺️ *Введите Город:*", parse_mode="Markdown")
    await state.set_state(OrderForm.city)
    await asyncio.sleep(1.3)
    await temp_mess.delete()
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="city"
    )


@processing.message(OrderForm.city)
async def process_city(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    formatted_city = message.text.strip().lower().capitalize()
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="city",
        data=formatted_city,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text_address = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    new_hint = await message.answer("🛣️ *Введите Улицу:*", parse_mode="Markdown")
    await state.set_state(OrderForm.street)
    await asyncio.sleep(1.3)
    await temp_mess.delete()
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="street"
    )


@processing.message(OrderForm.street)
async def process_street(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    formatted_street = message.text.strip().lower().capitalize()
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="street",
        data=formatted_street,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text_address = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    new_hint = await message.answer("🏠 *Введите Номер дома:*", parse_mode="Markdown")
    await state.set_state(OrderForm.house)
    await asyncio.sleep(1)
    await temp_mess.delete()
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="house"
    )


@processing.message(OrderForm.house)
async def process_house(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="house",
        data=message.text,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text_address = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    new_hint = await message.answer(
        "🚪 *Введите Номер квартиры:*",
        parse_mode="Markdown",
        reply_markup=await OrderProcessing.kb_skip_state(),
    )
    await state.set_state(OrderForm.apartment)
    await asyncio.sleep(1)
    await temp_mess.delete()
    await state.update_data(
        last_hint_id=new_hint.message_id, user_messages=[], current_step="apartment"
    )


@processing.message(OrderForm.apartment)
async def process_apartment(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data["last_hint_id"]
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="apartment",
        data=message.text,
    )
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text_address = await text_address_data(address_data, is_complete)
    is_complete = OrderQueries.check_address_completion(address_id)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    await state.clear()
    await asyncio.sleep(1.2)
    await temp_mess.delete()
