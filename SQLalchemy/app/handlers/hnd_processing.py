from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from utils.states import OrderForm
from aiogram.fsm.context import FSMContext
from queries.orm import OrderQueries, UserQueries, BookQueries
from text_templates import order_data_structure, text_address_data
from keyboards.kb_order import OrderProcessing
from config import ADMIN_ID
import asyncio

processing = Router()


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


async def format_address(address_data) -> str:
    if not address_data:
        return "Не указан"
    if hasattr(address_data, "_mapping"):
        address_dict = dict(address_data._mapping)
    else:
        address_dict = address_data
    parts = []
    if address_dict.get("city"):
        parts.append(f"г.{address_dict['city']}")
    if address_dict.get("street"):
        parts.append(f"ул.{address_dict['street']}")
    if address_dict.get("house"):
        parts.append(f"д.{address_dict['house']}")
    if address_dict.get("apartment"):
        parts.append(f"кв.{address_dict['apartment']}")
    return ", ".join(parts) if parts else "Не указан"


async def format_products(cart_data) -> str:
    products = []
    for item in cart_data:
        product_text = f"{item['book']} × {item['quantity']}шт. - {item['price']}₽"
        products.append(product_text)
    return "\n".join(products) if products else "Нет товаров"


async def send_order_notification(bot: Bot, order_data: dict, order_id):
    message_text = (
        "🛒 *НОВЫЙ ЗАКАЗ!*\n\n"
        f"👤 *Клиент:* {order_data['username']}\n"
        f"📞 *Телефон:* {order_data['user_phone']}\n"
        f"👤 *TG:* @{order_data['username']} (ID: {order_data['user_id']})\n"
        f"🏠 *Адрес:* {order_data['address']}\n"
        f"📦 *Товары:*\n{order_data['products']}\n"
        f"💰 *Сумма:* {order_data['total_price']}₽\n"
        f"💬 *Комментарий:* {order_data['comment']}\n"
        f"*Номер заказа* {order_id}"
    )
    try:
        await bot.send_message(
            chat_id=ADMIN_ID, text=message_text, parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")


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
        main_message_id=main_message.message_id,
        last_hint_id=hint_message.message_id,
        user_messages=[],
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
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    await asyncio.sleep(1.3)
    await temp_mess.delete()


@processing.callback_query(F.data.startswith("edit_address_"))
async def edit_address(callback: CallbackQuery, state: FSMContext):
    address_id_str = callback.data.split("_")[2]
    address_id = int(address_id_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    text = await text_address_data(address_data)
    is_complete = await OrderQueries.check_address_completion(address_id)
    if not is_complete:
        next_field = await OrderQueries.get_next_empty_field(address_id, telegram_id)
        await state.update_data(
            address_id=address_id,
            current_step=next_field,
            main_message_id=callback.message.message_id,
        )
        field_to_state = {
            "name": OrderForm.name,
            "phone": OrderForm.phone,
            "city": OrderForm.city,
            "street": OrderForm.street,
            "house": OrderForm.house,
            "apartment": OrderForm.apartment,
            "payment": OrderForm.payment,
            "comment": OrderForm.comment,
        }
        await state.set_state(field_to_state[next_field])
        prompts = {
            "name": "👤 Введите ваше имя:",
            "phone": "📞 Введите ваш телефон:",
            "city": "🏙️ Введите город:",
            "street": "🛣️ Введите улицу:",
            "house": "🏠 Введите номер дома:",
            "apartment": "🚪 Введите номер квартиры:",
            "payment": "💳 Выберите способ оплаты:",
            "comment": "💭 Введите комментарий:",
        }
        hint = await callback.message.answer(prompts[next_field])
        await state.update_data(last_hint_id=hint.message_id)
        await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    await callback.answer()


@processing.callback_query(F.data == "choose_address")
async def choose_address(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    addresses = await OrderQueries.get_address_small(telegram_id)
    await callback.message.edit_text(
        "🚚Выберите адрес доставки:",
        reply_markup=await OrderProcessing.kb_choose_address(addresses),
    )


@processing.callback_query(F.data.startswith("what_to_change_"))
async def choose_change(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    address_str = callback.data.split("_")[3]
    address_id = int(address_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    address_text = await text_address_data(address_data)
    address_text += "✏️Выберите что вы хотите изменить или добавить"
    is_complete = await OrderQueries.check_address_completion(address_id)
    await callback.message.edit_text(
        address_text,
        reply_markup=await OrderProcessing.order_details(address_id, is_complete),
    )


@processing.callback_query(F.data.startswith("change_"))
async def change_details(callback: CallbackQuery, state: FSMContext):
    column = callback.data.split("_")[1]
    address_str = callback.data.split("_")[2]
    address_id = int(address_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    address_text = await text_address_data(address_data)
    address_text += "✏️Выберите что вы хотите изменить или добавить"
    await state.update_data(
        address_id=address_id,
        editing_column=column,
        message_id=callback.message.message_id,
    )
    await state.set_state(OrderForm.editing_field)
    prompts = {
        "name": "👤 Введите ваше имя:",
        "phone": "📞 Введите ваш телефон:",
        "city": "🗺️ Введите город:",
        "street": "🛣️ Введите улицу:",
        "house": "🏠 Введите номер дома:",
        "apartment": "🚪 Введите номер квартиры:",
        "payment": "💳 Выберите способ оплаты:",
        "comment": "💭 Введите комментарий:",
    }
    hint = await callback.message.answer(prompts[column])
    await state.update_data(last_hint_id=hint.message_id, user_messages=[])
    await callback.answer()


@processing.callback_query(F.data.startswith("delete_address_"))
async def ps_delete_address(callback: CallbackQuery):
    address_id = callback.data.split("_")[2]
    await callback.message.edit_text(
        "Вы уверены что хотите удалить адрес доставки ?",
        reply_markup=await OrderProcessing.kb_delete_address(address_id),
    )


@processing.callback_query(F.data.startswith("sure_delete_address_"))
async def sure_delete_address(callback: CallbackQuery, state: FSMContext):
    address_id = callback.data.split("_")[3]
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    address_int = int(address_id)
    await OrderQueries.delete_address_orm(address_int)
    await callback.message.edit_text(
        "✅Адрес успешно удален", reply_markup=await OrderProcessing.kb_after_delete()
    )


@processing.callback_query(F.data.startswith("complete_address_"))
async def done_address(callback: CallbackQuery, state: FSMContext):
    address_str = callback.data.split("_")[2]
    address_id = int(address_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    address_text = await text_address_data(address_data)
    current_state = await state.get_state()
    if current_state:
        data = await state.get_data()
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            bot = callback.bot
            await delete_messages(bot, callback.message.chat.id, [last_hint_id])
        await state.clear()
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    price = int(total_price)
    list_of_books = []
    for book_data in cart_data:
        books_inside = (
            f"\n📖{book_data['book']} {book_data['quantity']}шт.  {book_data['price']}₽"
        )
        list_of_books.append(books_inside)
    user_balance = await UserQueries.get_user_balance(telegram_id)
    balance = int(user_balance)
    text = f"    🛒Корзина\n{''.join(list_of_books)}\n\n💳 Ваш баланс - {user_balance}₽\n💵 Сумма корзины -  {total_price}₽"
    text += address_text
    remainder = balance - price
    if remainder >= 0:
        await callback.message.edit_text(
            text,
            reply_markup=await OrderProcessing.kb_confirm_order(
                remainder,
                address_id,
            ),
        )
    else:
        text += f"\n❗На балансе недостаточно({-remainder}₽) средств для покупки"
        await callback.message.edit_text(
            text,
            reply_markup=await OrderProcessing.kb_confirm_order(
                remainder,
                address_id,
            ),
        )


@processing.callback_query(F.data.startswith("new_order_done_"))
async def new_order_done(callback: CallbackQuery, bot: Bot):
    wait_msg = await callback.message.answer("Обработка заказа ⏳")
    address_str = callback.data.split("_")[3]
    address_id = int(address_str)
    telegram_id = callback.from_user.id
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    price = int(total_price)
    user_balance = await UserQueries.get_user_balance(telegram_id)
    balance = int(user_balance)
    remainder = balance - price
    if remainder >= 0:
        all_available, insufficient_books = await BookQueries.check_books_availability(
            cart_data
        )
        if all_available:
            if address_data:
                address_dict = dict(address_data._mapping)
            else:
                address_dict = {}
            order_data = {
                "user_name": address_dict.get("name", "Не указано"),
                "user_phone": address_dict.get("phone", "Не указан"),
                "address": await format_address(address_dict),
                "payment": address_dict.get("payment", "Не указан"),
                "products": await format_products(cart_data),
                "total_price": total_price,
                "comment": address_dict.get("comment", "Нет комментария"),
                "user_id": telegram_id,
                "username": callback.from_user.username or "Не указан",
            }
            await BookQueries.decrease_book_value(cart_data)
            await UserQueries.updata_user_balance(telegram_id, remainder)
            order_id = await OrderQueries.made_order(
                telegram_id, address_id, price, cart_data
            )
            await send_order_notification(bot, order_data, order_id)
            await OrderQueries.del_cart(telegram_id)
            await wait_msg.delete()
            await callback.message.edit_text(
                text=f"🎊 Заказ оформлен! 🎊\nНомер вашего заказа {order_id}\nВ Ближайшее время с вам свяжется менеджер для согласования даты доставки\nСледить за статусом заказа можно в разделе: 📦 Мои заказы",
                reply_markup=await OrderProcessing.kb_order_last_step(
                    remainder, all_available, address_id
                ),
            )
        else:
            await wait_msg.delete()
            await callback.message.edit_text(
                text=f"❌ Произошла Ошибка, у нас не хватает книг\n\n{''.join(insufficient_books)}\n\nПожалуйста, вернитесь в главное корзину и повторите попытку.",
                reply_markup=await OrderProcessing.kb_order_last_step(
                    remainder, all_available, address_id
                ),
            )
    else:
        await wait_msg.delete()
        await callback.message.edit_text(
            text=f"❌ На вашем балансе не хватает {-remainder}₽ для заказа",
            reply_markup=await OrderProcessing.kb_order_last_step(
                remainder, all_available, address_id
            ),
        )


# FMScontext hnd


@processing.message(OrderForm.editing_field)
async def process_editing_field(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    column = data["editing_column"]
    main_message_id = data["message_id"]
    last_hint_id = data.get("last_hint_id")
    user_messages = data.get("user_messages", [])
    user_messages.append(message.message_id)
    if last_hint_id:
        await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    formatted_data = message.text.strip()
    if column in ["name", "city", "street"]:
        formatted_data = message.text.strip().lower().capitalize()
    await OrderQueries.update_info(
        message.from_user.id, address_id, column, formatted_data
    )
    is_complete = await OrderQueries.check_address_completion(address_id)
    address_data = await OrderQueries.get_user_address_data(
        message.from_user.id, address_id
    )
    text = await text_address_data(address_data)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text}",
        reply_markup=await OrderProcessing.order_details(address_id, is_complete),
        parse_mode="Markdown",
    )
    temp_msg = await message.answer("✅ Данные обновлены")
    await asyncio.sleep(1)
    await temp_msg.delete()
    await state.clear()


@processing.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    address_id = data["address_id"]
    main_message_id = data["main_message_id"]
    last_hint_id = data.get("last_hint_id")
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
    await asyncio.sleep(1)
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
    last_hint_id = data.get("last_hint_id")
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
    await asyncio.sleep(1)
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
    last_hint_id = data.get("last_hint_id")
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
    await asyncio.sleep(1)
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
    last_hint_id = data.get("last_hint_id")
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
    last_hint_id = data.get("last_hint_id")
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
    last_hint_id = data.get("last_hint_id")
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
    text_address = await text_address_data(address_data)
    is_complete = await OrderQueries.check_address_completion(address_id)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=main_message_id,
        text=f"{text_address}",
        reply_markup=await OrderProcessing.kb_change_details(address_id, is_complete),
    )
    temp_mess = await message.answer("✅ *Данные обновлены*", parse_mode="Markdown")
    await asyncio.sleep(1)
    await temp_mess.delete()
    await state.clear()
