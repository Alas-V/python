from aiogram import Bot, Router, F, types
from aiogram.types import Message, CallbackQuery
from utils.states import OrderForm
from aiogram.fsm.context import FSMContext
from queries.orm import OrderQueries, UserQueries, BookQueries, AdminQueries
from text_templates import order_data_structure, text_address_data
from keyboards.kb_order import OrderProcessing
from keyboards.kb_admin import KbAdmin
from config import PAYMENT_TOKEN
import asyncio
from models import AdminPermission
from aiogram.types.message import ContentType
import logging
import asyncio
import time
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.filters import StateFilter
from aiogram.enums import ContentType
import regex as re

pending_payments = {}

processing = Router()

payment_logger = logging.getLogger("payment")


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(
                e
            ) and "message can't be deleted" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


async def validate_field(column_name: str, value: str) -> tuple[bool, str, str]:
    if column_name == "name":
        if not value:
            return False, "", "❌ Имя не может быть пустым\n\n📝 Введите имя:"
        if len(value) < 2:
            return False, "", "❌ Имя слишком короткое (минимум 2 символа)"
        if len(value) > 100:
            return False, "", "❌ Имя слишком длинное (максимум 100 символов)"
        if not re.match(r"^[\p{L}\s\-\'\.]+$", value, re.UNICODE):
            return (
                False,
                "",
                "❌ Имя содержит недопустимые символы\n\n✅ Можно использовать буквы любого алфавита, пробелы, дефис, апостроф, точку",
            )
        if (
            len(
                set(
                    value.lower()
                    .replace(" ", "")
                    .replace("-", "")
                    .replace("'", "")
                    .replace(".", "")
                )
            )
            < 2
        ):
            return False, "", "❌ Имя выглядит некорректно"
        value = " ".join(value.split())
        words = re.split(r"([\s\-\']+)", value)
        formatted_parts = []
        for word in words:
            if word and not word.isspace() and word not in "-'":
                formatted_parts.append(word.capitalize())
            else:
                formatted_parts.append(word)
        return True, "".join(formatted_parts), ""
    elif column_name == "phone":
        if not value:
            return False, "", "❌ Номер телефона не может быть пустым"
        phone_digits = "".join(filter(str.isdigit, value))
        if not phone_digits:
            return False, "", "❌ Номер телефона должен содержать цифры"
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            return (
                False,
                "",
                f"❌ Неверная длина номера. Получено {len(phone_digits)} цифр, должно быть 10-15",
            )
        if phone_digits.startswith("8"):
            phone_digits = "7" + phone_digits[1:]
            phone_number = "+" + phone_digits
        elif phone_digits.startswith("7") and not value.startswith("+"):
            phone_number = "+" + phone_digits
        elif len(phone_digits) == 10:
            phone_number = "+7" + phone_digits
        else:
            phone_number = value if value.startswith("+") else "+" + phone_digits
        return True, phone_number, ""
    elif column_name == "city":
        if not value:
            return False, "", "❌ Город не может быть пустым\n\n🏙️ Введите город:"
        if len(value) < 2:
            return False, "", "❌ Название города слишком короткое (минимум 2 символа)"
        if len(value) > 100:
            return (
                False,
                "",
                "❌ Название города слишком длинное (максимум 100 символов)",
            )
        if re.search(r"\d", value):
            return False, "", "❌ В названии города не должно быть цифр"
        if not re.match(r"^[\p{L}\s\-\.]+$", value, re.UNICODE):
            return False, "", "❌ Название города содержит недопустимые символы"
        formatted_city = " ".join(word.capitalize() for word in value.split())
        return True, formatted_city, ""
    elif column_name == "street":
        if not value:
            return False, "", "❌ Улица не может быть пустой\n\n🛣️ Введите улицу:"
        if len(value) < 2:
            return False, "", "❌ Название улицы слишком короткое (минимум 2 символа)"
        if len(value) > 100:
            return (
                False,
                "",
                "❌ Название улицы слишком длинное (максимум 100 символов)",
            )
        if re.search(r'[@#$%^&*()_+={}\[\]:;"<>?/~`]', value):
            return False, "", "❌ Название улицы содержит недопустимые символы"
        words = value.split()
        formatted_words = []
        for word in words:
            if re.match(r"^[IVXLCDM]+$", word.upper()):
                formatted_words.append(word.upper())
            elif re.search(r"\d", word):
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())
        formatted_street = " ".join(formatted_words)
        return True, formatted_street, ""
    elif column_name == "house":
        if not value:
            return (
                False,
                "",
                "❌ Номер дома не может быть пустым\n\n🏠 Введите номер дома:",
            )
        if len(value) > 20:
            return False, "", "❌ Номер дома слишком длинный (максимум 20 символов)"
        if not re.match(r"^\d", value):
            return False, "", "❌ Номер дома должен начинаться с цифры"
        if not re.match(r"^[\dа-яА-Яa-zA-Z\/\-\.\s]+$", value):
            return False, "", "❌ Номер дома содержит недопустимые символы"
        return True, value, ""
    elif column_name == "apartment":
        if not value:
            return True, None, ""
        if len(value) > 10:
            return False, "", "❌ Номер квартиры слишком длинный (максимум 10 символов)"
        if not re.match(r"^[\dа-яА-Яa-zA-Z]+$", value):
            return False, "", "❌ Номер квартиры содержит недопустимые символы"
        return True, value, ""
    else:
        return True, value, ""


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


async def send_order_notification(bot: Bot, order_data: dict, order_id: int):
    comment = order_data.get("comment")
    if comment is None:
        comment = "Не указан"
    message_text = (
        "🛒 *НОВЫЙ ЗАКАЗ!*\n\n"
        f"👤 *Клиент:* {order_data['username']}\n"
        f"📞 *Телефон:* {order_data['user_phone']}\n"
        f"👤 *TG:* @{order_data['username']} (ID: {order_data['user_id']})\n"
        f"🏠 *Адрес:* {order_data['address']}\n"
        f"📦 *Товары:*\n{order_data['products']}\n"
        f"💰 *Сумма:* {order_data['total_price']}₽\n"
        f"💬 *Комментарий:* {comment}\n"
        f"*Номер заказа* {order_id}"
    )
    try:
        admin_ids = await AdminQueries.get_admins_with_permission(
            AdminPermission.MANAGE_ORDERS
        )
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message_text,
                    parse_mode="Markdown",
                    reply_markup=await KbAdmin.kb_open_order_for_admin(order_id),
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления админу {admin_id}: {e}")
                continue
    except Exception as e:
        print(f"Ошибка при получении списка админов: {e}")


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
        "name": "👤 Введите имя получателя:",
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
        text += f"\n❗На балансе недостаточно средств ({-remainder}₽) для покупки"
        main_message = await callback.message.edit_text(
            text,
            reply_markup=await OrderProcessing.kb_confirm_order(
                remainder,
                address_id,
            ),
        )
        await state.update_data(
            remainder=-remainder,
            main_message_id=main_message.message_id,
            list_of_books=list_of_books,
            telegram_id=telegram_id,
            address_id=address_id,
            username=callback.from_user.username,
        )


@processing.callback_query(F.data.startswith("replenish_balance_"))
async def replenish_balance(callback: CallbackQuery, bot: Bot, state: FSMContext):
    address_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    remainder = data.get("remainder")
    main_message_id = data.get("main_message_id")
    list_of_books = data.get("list_of_books")
    telegram_id = data.get("telegram_id")
    user_balance = await UserQueries.get_user_balance(telegram_id)
    balance = int(user_balance)
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    price = int(total_price)
    remainder = balance - price
    if main_message_id:
        try:
            await delete_messages(
                bot=bot, chat_id=callback.message.chat.id, message_ids=[main_message_id]
            )
        except Exception as e:
            print(f"error in replenish_balance : {e}")
    payment_id = f"pay_{telegram_id}_{int(time.time())}"
    pending_payments[payment_id] = {
        "user_id": telegram_id,
        "address_id": address_id,
        "created_at": time.time(),
        "status": "pending",
    }
    invoice = await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Покупка в магазине Book_bot",
        description="".join(list_of_books) if list_of_books else "Пополнение баланса",
        provider_token=PAYMENT_TOKEN,
        currency="rub",
        is_flexible=False,
        prices=[LabeledPrice(label="Пополнение баланса", amount=int(-remainder * 100))],
        payload=payment_id,
        photo_url="https://thumbs.dreamstime.com/b/%D0%BA%D0%BD%D0%B8%D0%B6%D0%BD%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BB%D0%BA%D0%B8-%D0%B4%D1%80%D0%B5%D0%B2%D0%BD%D0%B5%D0%B9-%D0%B2%D0%B5%D0%BD%D1%81%D0%BA%D0%BE%D0%B9-%D0%B1%D0%B8%D0%B1%D0%BB%D0%B8%D0%BE%D1%82%D0%B5%D0%BA%D0%B8-%D0%B0%D0%B2%D1%81%D1%82%D1%80%D0%B8%D1%8F-%D0%B2%D0%B5%D0%BD%D0%B0-%D1%81%D0%B5%D0%BD%D1%82%D1%8F%D0%B1%D1%80%D1%8C-%D0%B3%D0%BE%D0%B4%D0%B0-308270038.jpg",
        photo_height=450,
        photo_width=800,
        photo_size=100000,
    )
    await state.update_data(price=-remainder, invoice_message_id=invoice.message_id)
    asyncio.create_task(
        cancel_payment_after_timeout(bot, payment_id, telegram_id, invoice.message_id)
    )


async def cancel_payment_after_timeout(
    bot: Bot, payment_id: str, user_id: int, invoice_message_id: int, timeout: int = 900
):
    await asyncio.sleep(timeout)
    if (
        payment_id in pending_payments
        and pending_payments[payment_id]["status"] == "pending"
    ):
        pending_payments[payment_id]["status"] = "timeout"
        try:
            await bot.delete_message(chat_id=user_id, message_id=invoice_message_id)
            print(f"Инвойс {invoice_message_id} удален по таймауту")
        except Exception as e:
            print(f"Не удалось удалить инвойс при таймауте: {e}")
        await asyncio.sleep(3600)
        if payment_id in pending_payments:
            del pending_payments[payment_id]


@processing.pre_checkout_query()
async def pre_checkout_query_handler(
    pre_checkout_q: PreCheckoutQuery, state: FSMContext, bot: Bot
):
    try:
        payment_id = pre_checkout_q.invoice_payload
        if payment_id not in pending_payments:
            await pre_checkout_q.answer(
                ok=False, error_message="Платеж устарел. Создайте новый."
            )
            return
        payment_data = pending_payments[payment_id]
        amount_expected = payment_data.get("amount", 0) * 100
        if amount_expected == 0:
            data = await state.get_data()
            telegram_id = data.get("telegram_id")
            user_balance = await UserQueries.get_user_balance(telegram_id)
            total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
            amount_expected = max(0, total_price - user_balance) * 100
        if pre_checkout_q.total_amount != amount_expected:
            await pre_checkout_q.answer(
                ok=False, error_message="Неверная сумма платежа"
            )
            return
        if pre_checkout_q.currency != "RUB":
            await pre_checkout_q.answer(ok=False, error_message="Неверная валюта")
            return
        data = await state.get_data()
        telegram_id = data.get("telegram_id")
        total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
        all_available, insufficient_books = await BookQueries.check_books_availability(
            cart_data
        )
        if all_available:
            await pre_checkout_q.answer(ok=True)
        else:
            await pre_checkout_q.answer(
                ok=False,
                error_message=f"Товары закончились: {', '.join(insufficient_books)}",
            )
    except Exception as e:
        print(f"Error in pre_checkout_query: {e}")
        await pre_checkout_q.answer(ok=False, error_message="Ошибка проверки")


@processing.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    address_id = data.get("address_id")
    username = data.get("username")
    invoice_message_id = data.get("invoice_message_id")
    if invoice_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=invoice_message_id
            )
            print(f"Инвойс {invoice_message_id} удален после оплаты")
        except Exception as e:
            print(f"Не удалось удалить инвойс: {e}")
    total_price, cart_data = await OrderQueries.get_cart_total(telegram_id)
    price = int(total_price)
    all_available, insufficient_books = await BookQueries.check_books_availability(
        cart_data
    )
    if not all_available:
        await message.answer(
            f"❌ Товары закончились: {', '.join(insufficient_books)}\n"
            f"Свяжитесь с администратором для возврата средств."
        )
        return
    address_data = await OrderQueries.get_user_address_data(telegram_id, address_id)
    address_dict = dict(address_data._mapping)
    order_data = {
        "user_name": address_dict.get("name", "Не указано"),
        "user_phone": address_dict.get("phone", "Не указан"),
        "address": await format_address(address_dict),
        "payment": address_dict.get("payment", "Не указан"),
        "products": await format_products(cart_data),
        "total_price": total_price,
        "comment": address_dict.get("comment", "Нет комментария"),
        "user_id": telegram_id,
        "username": username or "Не указан",
    }
    payment_amount = message.successful_payment.total_amount / 100
    await UserQueries.updata_user_balance(telegram_id, payment_amount)
    await BookQueries.decrease_book_value(cart_data)
    await UserQueries.updata_user_balance(telegram_id, 0)
    order_id = await OrderQueries.made_order(telegram_id, address_id, price, cart_data)
    await send_order_notification(bot, order_data, order_id)
    await OrderQueries.del_cart(telegram_id)
    payment_id = message.successful_payment.invoice_payload
    if payment_id in pending_payments:
        del pending_payments[payment_id]
    await message.answer(
        text=f"🎊 Заказ оформлен! 🎊\n\nНомер вашего заказа {order_id}\n\nВ Ближайшее время с вам свяжется менеджер для согласования даты доставки\n\nСледить за статусом заказа можно в разделе: 📦 Мои заказы",
        reply_markup=await OrderProcessing.kb_order_last_step(0, True, address_id),
    )


@processing.callback_query(F.data.startswith("cancel_payment_"))
async def cancel_payment(callback: CallbackQuery, bot: Bot, state: FSMContext):
    payment_id = callback.data.split("_")[-1]
    if payment_id in pending_payments:
        del pending_payments[payment_id]
        await callback.answer("Платеж отменен", show_alert=True)
        await callback.message.edit_text(
            "Платеж был отменен. Вы можете попробовать снова или изменить содержимое корзины."
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
                text=f"🎊 Заказ оформлен! 🎊\n\nНомер вашего заказа {order_id}\n\nВ Ближайшее время с вам свяжется менеджер для согласования даты доставки\n\nСледить за статусом заказа можно в разделе: 📦 Мои заказы",
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
    input_data = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    is_valid, formatted_data, error_message = await validate_field(column, input_data)
    if not is_valid:
        hints = {
            "name": "👤 Введите имя получателя:",
            "phone": "📞 Введите телефон:",
            "city": "🗺️ Введите город:",
            "street": "🛣️ Введите улицу:",
            "house": "🏠 Введите номер дома:",
            "apartment": "🚪 Введите номер квартиры (или оставьте пустым):",
        }
        error_msg = await message.answer(error_message)
        messages_to_delete = []
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            new_hint = await message.answer(
                hints.get(column, f"Введите значение для {column}:")
            )
            await state.update_data(
                last_hint_id=new_hint.message_id,
                user_messages=[],
                error_msg_id=error_msg.message_id,
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            await state.update_data(
                user_messages=user_messages, error_msg_id=error_msg.message_id
            )
        await state.set_state(OrderForm.editing_field)
        return
    if last_hint_id:
        try:
            await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    try:
        await OrderQueries.update_info(
            message.from_user.id, address_id, column, formatted_data
        )
    except Exception as e:
        print(f"Ошибка сохранения {column}: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
    name = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(last_hint_id=last_hint.message_id)
    if not name:
        error_msg = await message.answer(
            "❌ Имя не может быть пустым\n\n📝 Введите имя:"
        )
        await state.set_state(OrderForm.name)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(name) < 2:
        error_msg = await message.answer("❌ Имя слишком короткое (минимум 2 символа)")
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.name)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(name) > 100:
        error_msg = await message.answer(
            "❌ Имя слишком длинное (максимум 100 символов)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.name)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if not re.match(r"^[\p{L}\s\-\'\.]+$", name, re.UNICODE):
        error_msg = await message.answer(
            "❌ Имя содержит недопустимые символы\n\n"
            "✅ Можно использовать:\n"
            "• Буквы любого алфавита\n"
            "• Пробелы\n"
            "• Дефис (-)\n"
            "• Апостроф (') \n"
            "• Точку (.)\n\n"
            "🚫 Нельзя: цифры, скобки, @, #, $ и другие символы"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="👤 Введите имя получателя:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.name)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if (
        len(
            set(
                name.lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("'", "")
                .replace(".", "")
            )
        )
        < 2
    ):
        error_msg = await message.answer("❌ Имя выглядит некорректно")
        await state.set_state(OrderForm.name)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    name = " ".join(name.split())
    words = re.split(r"([\s\-\']+)", name)
    formatted_parts = []
    for word in words:
        if word and not word.isspace() and word not in "-'":
            formatted_parts.append(word.capitalize())
        else:
            formatted_parts.append(word)
    formatted_name = "".join(formatted_parts)
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="name",
            data=formatted_name,
        )
    except Exception as e:
        print(f"Ошибка сохранения имени: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
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
    if last_hint_id:
        try:
            await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
        except Exception:
            pass
    temp_mess = await message.answer("✅ Имя сохранено")
    new_hint = await message.answer("📞 Введите телефон:")
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
    phone_number = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    error_message = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    if not phone_number:
        error_message = "❌ Номер телефона не может быть пустым"
    else:
        phone_digits = "".join(filter(str.isdigit, phone_number))
        if not phone_digits:
            error_message = "❌ Номер телефона должен содержать цифры"
        else:
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                error_message = f"❌ Неверная длина номера. Получено {len(phone_digits)} цифр, должно быть 10-15"
            else:
                if phone_digits.startswith("8"):
                    phone_digits = "7" + phone_digits[1:]
                    phone_number = "+" + phone_digits
                elif phone_digits.startswith("7") and not phone_number.startswith("+"):
                    phone_number = "+" + phone_digits
                if len(phone_digits) == 10:
                    phone_number = "+7" + phone_digits
    if error_message:
        error_msg = await message.answer(error_message)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="📞 Введите ваш телефон:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="📞 Введите ваш телефон:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.phone)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="phone",
            data=phone_number,
        )
    except Exception as e:
        print(f"Ошибка сохранения телефона: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    city = message.text.strip()
    if not city:
        error_msg = await message.answer(
            "❌ Город не может быть пустым\n\n🏙️ Введите город:"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.city)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(city) < 2:
        error_msg = await message.answer(
            "❌ Название города слишком короткое (минимум 2 символа)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.city)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(city) > 100:
        error_msg = await message.answer(
            "❌ Название города слишком длинное (максимум 100 символов)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.city)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if re.search(r"\d", city):
        error_msg = await message.answer(
            "❌ В названии города не должно быть цифр\n\n"
            "🏙️ Укажите только название города\n"
            "📍 Номер дома указывается в следующем шаге"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.city)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if not re.match(r"^[\p{L}\s\-\.]+$", city, re.UNICODE):
        error_msg = await message.answer(
            "❌ Название города содержит недопустимые символы\n\n"
            "✅ Можно использовать:\n"
            "• Буквы любого алфавита\n"
            "• Пробелы\n"
            "• Дефис (-)\n"
            "• Точку (.)\n\n"
            "🚫 Нельзя: цифры, апострофы, скобки и другие символы"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🗺️ Введите город:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.city)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    formatted_city = " ".join(word.capitalize() for word in city.split())
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="city",
            data=formatted_city,
        )
    except Exception as e:
        print(f"Ошибка сохранения города: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
    street = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    if not street:
        error_msg = await message.answer(
            "❌ Улица не может быть пустой\n\n🛣️ Введите улицу:"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.street)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(street) < 2:
        error_msg = await message.answer(
            "❌ Название улицы слишком короткое (минимум 2 символа)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.street)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(street) > 100:
        error_msg = await message.answer(
            "❌ Название улицы слишком длинное (максимум 100 символов)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.street)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if re.search(r'[@#$%^&*()_+={}\[\]:;"<>?/~`]', street):
        error_msg = await message.answer(
            "❌ Название улицы содержит недопустимые символы\n\n"
            "✅ Можно использовать:\n"
            "• Буквы и цифры\n"
            "• Пробелы\n"
            "• Дефис (-), точку (.), запятую (,), апостроф (')\n\n"
            "🚫 Нельзя: @ # $ % ^ & * и другие спецсимволы"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🛣️ Введите улицу:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.street)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    words = street.split()
    formatted_words = []
    for word in words:
        if re.match(r"^[IVXLCDM]+$", word.upper()):
            formatted_words.append(word.upper())
        elif re.search(r"\d", word):
            formatted_words.append(word)
        else:
            formatted_words.append(word.capitalize())
    formatted_street = " ".join(formatted_words)
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="street",
            data=formatted_street,
        )
    except Exception as e:
        print(f"Ошибка сохранения улицы: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
        "🏠 *Введите Номер дома:*",
        parse_mode="Markdown",
    )
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
    house = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    if not house:
        error_msg = await message.answer(
            "❌ Номер дома не может быть пустым\n\n🏠 Введите номер дома:"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.house)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if len(house) > 20:
        error_msg = await message.answer(
            "❌ Номер дома слишком длинный (максимум 20 символов)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.house)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if not re.match(r"^\d", house):
        error_msg = await message.answer(
            "❌ Номер дома должен начинаться с цифры\n\n"
            "✅ Примеры правильных форматов:\n"
            "• 12 (просто число)\n"
            "• 15А (число и буква)\n"
            "• 24/2 (дробный номер)\n"
            "• 7-Б (число, дефис, буква)"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.house)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    if not re.match(r"^[\dа-яА-Яa-zA-Z\/\-\.\s]+$", house):
        error_msg = await message.answer(
            "❌ Номер дома содержит недопустимые символы\n\n"
            "✅ Можно использовать:\n"
            "• Цифры 0-9\n"
            "• Буквы (русские и английские)\n"
            "• Слэш (/), дефис (-), точку (.)\n\n"
            "🚫 Нельзя: @ # $ % ^ & * и другие спецсимволы"
        )
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(
                last_hint_id=last_hint.message_id, user_messages=[], error_msg_id=None
            )
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
            last_hint = await message.answer(text="🏠 Введите номер дома:")
            await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(OrderForm.house)
        await state.update_data(
            user_messages=user_messages, error_msg_id=error_msg.message_id
        )
        return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="house",
            data=house,
        )
    except Exception as e:
        print(f"Ошибка сохранения номера дома: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
        "🚪 *Введите Номер квартиры:*\n\n_Если нет квартиры - нажмите 'Пропустить'_",
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
    apartment = message.text.strip()
    error_msg_id = data.get("error_msg_id")
    messages_to_delete = []
    if error_msg_id:
        messages_to_delete.append(error_msg_id)
        if last_hint_id:
            messages_to_delete.append(last_hint_id)
        messages_to_delete.extend(user_messages)
        try:
            await delete_messages(bot, message.chat.id, messages_to_delete)
            await state.update_data(user_messages=[], error_msg_id=None)
        except Exception as e:
            print(f"Ошибка удаления сообщений: {e}")
    if apartment:
        if len(apartment) > 10:
            error_msg = await message.answer(
                "❌ Номер квартиры слишком длинный (максимум 10 символов)"
            )
            if last_hint_id:
                messages_to_delete.append(last_hint_id)
            messages_to_delete.extend(user_messages)
            try:
                await delete_messages(bot, message.chat.id, messages_to_delete)
                last_hint = await message.answer(text="🚪 Введите номер квартиры:")
                await state.update_data(
                    last_hint_id=last_hint.message_id,
                    user_messages=[],
                    error_msg_id=None,
                )
            except Exception as e:
                print(f"Ошибка удаления сообщений: {e}")
                last_hint = await message.answer(text="🚪 Введите номер квартиры:")
                await state.update_data(last_hint_id=last_hint.message_id)
            await state.set_state(OrderForm.apartment)
            await state.update_data(
                user_messages=user_messages, error_msg_id=error_msg.message_id
            )
            return
        if not re.match(r"^[\dа-яА-Яa-zA-Z]+$", apartment):
            error_msg = await message.answer(
                "❌ Номер квартиры содержит недопустимые символы\n\n"
                "✅ Можно использовать:\n"
                "• Цифры 0-9\n"
                "• Буквы (русские и английские)\n\n"
                "🚫 Нельзя: пробелы, дефисы, слэши и другие символы"
            )
            if last_hint_id:
                messages_to_delete.append(last_hint_id)
            messages_to_delete.extend(user_messages)
            try:
                await delete_messages(bot, message.chat.id, messages_to_delete)
                last_hint = await message.answer(text="🚪 Введите номер квартиры:")
                await state.update_data(
                    last_hint_id=last_hint.message_id,
                    user_messages=[],
                    error_msg_id=None,
                )
            except Exception as e:
                print(f"Ошибка удаления сообщений: {e}")
                last_hint = await message.answer(text="🚪 Введите номер квартиры:")
                await state.update_data(last_hint_id=last_hint.message_id)
            await state.set_state(OrderForm.apartment)
            await state.update_data(
                user_messages=user_messages, error_msg_id=error_msg.message_id
            )
            return
    await delete_messages(bot, message.chat.id, [last_hint_id] + user_messages)
    try:
        is_complete = await OrderQueries.update_info(
            telegram_id=message.from_user.id,
            address_id=address_id,
            column="apartment",
            data=apartment if apartment else None,
        )
    except Exception as e:
        print(f"Ошибка сохранения номера квартиры: {e}")
        error_msg = await message.answer("❌ Ошибка сохранения. Попробуйте снова:")
        await asyncio.sleep(3)
        await error_msg.delete()
        return
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
