async def get_book_details(book_data: dict):
    rating = float(book_data.get("book_rating"))
    price = float(book_data.get("book_price"))

    return f"""
📖 <b>{book_data.get("book_title")}</b>

✍ Автор: <i>{book_data.get("author_name")}</i> 
🌎 {book_data.get("author_country")}
🗓 Год издания: {book_data.get("book_year")}
📦 Остаток в магазине: {book_data.get("book_quantity")} шт.

    {round(rating, 2)}⭐ 
    {book_data.get("reviews_count", 0)} отзывов

💳 <b>Цена:</b> {price}₽ 
"""


async def get_book_details_on_sale(book_data: dict):
    rating = float(book_data.get("book_rating", 0))
    price = float(book_data.get("book_price", 0))
    sale_value = float(book_data.get("sale_value", 0))
    new_price = round(price * (1 - sale_value), 2)
    discount_percent = round(100 * sale_value)
    return f"""
📖 <b>{book_data.get("book_title")}</b>

✍ Автор: <i>{book_data.get("author_name")}</i> 
🌎 {book_data.get("author_country")}
🗓 Год издания: {book_data.get("book_year")}
📦 Остаток в магазине: {book_data.get("book_quantity")} шт.

    {round(rating, 2)}⭐ 
    {book_data.get("reviews_count", 0)} отзывов

💳 <b>Цена:</b> <s>{price}₽</s> <b>{new_price}₽</b> (скидка {discount_percent}%)
"""


async def order_data_structure(list_of_books, total_price, order_data, user_balance):
    defaults = (None,) * 8
    name, phone, city, street, house, apartment, payment, comment = (
        order_data if order_data else defaults
    )
    name = name if name else "Не указано"
    phone = phone if phone else "Не указан"
    payment = payment if payment else "Не указан"
    comment = comment if comment else "Не указан"
    if city and street and house is not None:
        if apartment:
            address = f"г.{city}, {street}, {house}, {apartment}кв."
        else:
            address = f"г.{city}, {street}, {house}"
    else:
        address = "Не указан"
    return f"""
            🛒Корзина
{"".join(list_of_books)}


Ваш баланс - {user_balance}₽
Сумма корзины -  {total_price}₽


            📝 Текущие данные заказа: 

👤 Имя: {name}
📞 Номер телефона: {phone}
🏠 Адрес: {address}
💳 Способ оплаты: {payment}
💭 Комментарий: {comment}
"""


async def text_address_data(order_data):
    defaults = (None,) * 8
    name, phone, city, street, house, apartment, comment, is_complete = (
        order_data if order_data else defaults
    )
    name = name if name else "Не указано"
    phone = phone if phone else "Не указан"
    address_parts = []
    if city:
        address_parts.append(f"г.{city}")
    if street:
        address_parts.append(f"ул.{street}")
    if house:
        address_parts.append(f"д.{house}")
    if apartment:
        address_parts.append(f"кв.{apartment}")
    address = ", ".join(address_parts) if address_parts else "Не указан"
    if is_complete:
        completed_text = "  🚚 Данные доставки"
    else:
        completed_text = "📝 Заполните все необходимые данные доставки"
    if comment:
        comment_text = f"💭 Комментарий: {comment}"
    else:
        comment_text = ""
    return f""" 

        {completed_text}

👤 Имя: {name}
📞 Номер телефона: {phone}
🏠 Адрес: {address}
{comment_text}
"""


async def format_order_details(order_details: dict) -> str:
    return f"""
📦 *Заказ #{order_details["order_id"]}*

💰 *Сумма:* {order_details["total_price"]}₽
📋 *Статус:* {order_details["status"]}
📅 *Дата:* {order_details["created_date"].strftime("%d.%m.%Y %H:%M")}

🚚 *Адрес доставки:*
{order_details["address"]}

🛒 *Товары:*
{order_details["items"]}

💭 *Комментарий:* {order_details["comment"] or "Нет"}
"""


async def get_full_review(review_data, for_new=False):
    rating = review_data.get("review_rating")
    title = review_data.get("review_title")
    body = review_data.get("review_body")
    created_at = review_data["created_at"]
    rating_emoji = {0: "Нет оценки ", 1: "😠", 2: "😕", 3: "😐", 4: "🙂", 5: "😍"}.get(
        rating, "⭐"
    )
    stars = "⭐" * rating + "☆" * (5 - rating)
    date_str = created_at.strftime("%d.%m.%Y в %H:%M")
    title = title if title else "Заголовок не указан"
    body = body if body else "Нет основного текста отзыва"
    if for_new:
        date = ""
    else:
        date = f"📅 *Дата:* {date_str}"
    text = f"""
{rating_emoji} *{title}*

{stars} ({rating})

📖 *Текст отзыва:*
{body}

{date}
"""
    return text


async def book_for_review(book_info):
    message_text = (
        f"📖 <b>{book_info['book_title']}</b>\n"
        f"👤 Автор: {book_info['author_name'] or 'Неизвестен'}\n"
        f"⭐ Оценка: {book_info['avg_rating'] or 0:.1f}\n"
        f"💬 Количество отзывов: {book_info['reviews_count'] or 0}\n\n"
    )
    return message_text


async def appeal_hint_text(appeal_id: int):
    message_text = f"""
📝 *Обращение #{appeal_id} создано*

Опишите вашу проблему или вопрос, и мы ответим в ближайшее время.

💡 Укажите номер заказа, если вопрос связан с заказом

🕐 *Среднее время ответа:* 1-2 часа
"""
    return message_text


async def cooldown_text(cooldown_time):
    text = f"""📝 Следующее обращение можно создать через 🕐 **{cooldown_time} минут**

Мы ценим ваше внимание и стараемся ответить на все обращения максимально быстро. Небольшая пауза помогает нам сохранить качество поддержки.

💡 Вы можете дополнить ваше прошлое обращение"""
    return text


status_dict = {
    "in_work": "🔧 В работе",
    "closed_by_user": "✅ Вы закрыли это обращение",
    "closed_by_admin": "✅ Администратор закрыл это обращение ",
}


async def text_appeal_split_messages(appeal) -> tuple[list[str], str]:
    if not appeal:
        return [], "❌ Обращение не найдено"
    main_text = f"""📨 *Обращение #{appeal.appeal_id}*
🔄 Статус: {status_dict[appeal.status]}
📅 Создано: {appeal.created_date.strftime("%d.%m.%Y %H:%M")}
💬 Сообщений: {len(appeal.user_messages) + len(appeal.admin_messages)}
"""
    if not appeal.user_messages and not appeal.admin_messages:
        return [], main_text + "\n\n📭 *Пока нет сообщений*"
    all_messages = []
    for msg in appeal.user_messages:
        all_messages.append(("👤 Вы", msg.created_date, msg.user_message))
    for msg in appeal.admin_messages:
        all_messages.append(("🛠 Поддержка", msg.created_date, msg.admin_message))
    all_messages.sort(key=lambda x: x[1])
    single_message_text = main_text + "\n\n*История обращений:*\n\n"
    for sender, time, text in all_messages:
        message_line = f"{sender} ({time.strftime('%H:%M')}):\n{text}\n\n"
        single_message_text += message_line
    if len(single_message_text) <= 4000:
        return [], single_message_text
    message_parts = []
    current_part = "*История обращений:*\n\n"
    for sender, time, text in all_messages:
        message_line = f"{sender} ({time.strftime('%H:%M')}):\n{text}\n\n"
        if len(current_part) + len(message_line) > 4000:
            message_parts.append(current_part)
            current_part = "*Продолжение:*\n\n" + message_line
        else:
            current_part += message_line
    if current_part and current_part != "*История обращений:*\n\n":
        message_parts.append(current_part)
    return message_parts, main_text


INFOTEXT = """📚 BookStore Demo Bot
Прототип книжного магазина с полным циклом заказа

🔹 О проекте:
Демонстрационный бот, реализующий ключевые функции интернет-магазина:

    Каталог книг с фильтрами

    Корзина с учетом количества и стоимости

    История заказов

    Поиск по жанрам

⚙️ Технологии:

    Python 3.11 + AsyncIO

    SQLAlchemy 2.0 (асинхронная работа с PostgreSQL)

    Aiogram 3.x (Telegram Bot API)

    Алгоритмы эффективного поиска

🎯 Особенности реализации:

    Оптимизированные запросы к БД

    Интуитивная навигация (пагинация, inline-поиск)

    Гибкая система обработки платежей (демо-режим)

    Логирование и обработка ошибок

💼 Для заказчиков:

    Подход к проектированию сложных ботов

    Работу с реляционными базами данных

    Внимание к UX/UI в мессенджерах

Разработано (@sentrybuster) как пример промышленной реализации

[Готов адаптировать под ваши бизнес-задачи]"""
