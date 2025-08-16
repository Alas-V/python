
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


async def get_cart_and_order_details(cart_data: dict, order_data: dict):
    



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
