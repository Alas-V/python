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

pending_payments = {}

processing = Router()

payment_logger = logging.getLogger("payment")


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            await asyncio.sleep(0.1)
        except Exception as e:
            if "message to delete not found" not in str(
                e
            ) and "message can't be deleted" not in str(e):
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
        text=f"🎊 Заказ оформлен! 🎊\nНомер вашего заказа {order_id}\nВ Ближайшее время с вам свяжется менеджер для согласования даты доставки\nСледить за статусом заказа можно в разделе: 📦 Мои заказы",
        reply_markup=await OrderProcessing.kb_order_last_step(0, True, address_id),
    )


@processing.callback_query(F.data.startswith("cancel_payment_"))
async def cancel_payment(callback: CallbackQuery, bot: Bot, state: FSMContext):
    payment_id = callback.data.split("_")[-1]
    if payment_id in pending_payments:
        del pending_payments[payment_id]
        await callback.answer("Платеж отменен", show_alert=True)
        await callback.message.edit_text(
            "Платеж был отменен. Вы можете попробовать снова или изменить корзину."
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
    phone_number = message.text.strip()
    error_message = None
    try:
        phone_digits = "".join(filter(str.isdigit, phone_number))
        if not phone_digits:
            error_message = "❌ Номер телефона должен содержать цифры"
        else:
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                error_message = f"❌ Неверная длина номера. Получено {len(phone_digits)} цифр, должно быть 10-15"
            if phone_digits.startswith("8"):
                phone_digits = "7" + phone_digits[1:]
                phone_number = "+" + phone_digits
            elif phone_digits.startswith("7") and not phone_number.startswith("+"):
                phone_number = "+" + phone_digits
    except Exception as e:
        error_message = f"❌ Ошибка обработки номера: {str(e)}"
    if error_message:
        error_msg = await message.answer(error_message)
        new_hint = await message.answer(
            "📞 *Введите номер телефона:*", parse_mode="Markdown"
        )
        await state.set_state(OrderForm.phone)
        await asyncio.sleep(2)
        await error_msg.delete()
        await state.update_data(last_hint_id=new_hint.message_id, user_messages=[])
        return
    is_complete = await OrderQueries.update_info(
        telegram_id=message.from_user.id,
        address_id=address_id,
        column="phone",
        data=phone_number,
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
