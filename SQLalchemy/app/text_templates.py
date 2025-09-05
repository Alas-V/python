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
