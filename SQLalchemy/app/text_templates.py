from datetime import datetime


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
📝 Обращение #{appeal_id} создано

Опишите вашу проблему или вопрос, и мы ответим в ближайшее время.

💡 Укажите номер заказа, если вопрос связан с заказом

🕐 Среднее время ответа: 1-2 часа
"""
    return message_text


async def cooldown_text(cooldown_time):
    text = f"""📝 Следующее обращение можно создать через 🕐 **{cooldown_time} минут**

Мы ценим ваше внимание и стараемся ответить на все обращения максимально быстро. Небольшая пауза помогает нам сохранить качество поддержки.

💡 Вы можете дополнить ваше прошлое обращение"""
    return text


async def message_cooldown_text(seconds):
    if seconds < 60:
        if seconds == 1:
            return f"⏳ Подождите {seconds} секунду перед следующим сообщением"
        elif 2 <= seconds <= 4:
            return f"⏳ Подождите {seconds} секунды перед следующим сообщением"
        else:
            return f"⏳ Подождите {seconds} секунд перед следующим сообщением"
    else:
        minutes = (seconds + 59) // 60
        if minutes == 1:
            return f"⏳ Подождите {minutes} минуту перед следующим сообщением"
        elif 2 <= minutes <= 4:
            return f"⏳ Подождите {minutes} минуты перед следующим сообщением"
        else:
            return f"⏳ Подождите {minutes} минут перед следующим сообщением"


status_dict = {
    "new": "🆕 Новое",
    "in_work": "🔧 В работе",
    "closed_by_user": "✅ Вы закрыли это обращение",
    "closed_by_admin": "✅ Администратор закрыл это обращение ",
}


async def text_appeal_split_messages(appeal) -> tuple[list[str], str]:
    if not appeal:
        return [], "❌ Обращение не найдено"
    status_text = status_dict.get(appeal.status, appeal.status)
    main_text = f"""📨 *Обращение #{appeal.appeal_id}* {status_text}
📅 Создано: {appeal.created_date.strftime("%d.%m.%Y %H:%M")} 
"""
    if not appeal.user_messages and not appeal.admin_messages:
        return [], main_text + "\n\n📭 *Пока нет сообщений*"
    all_messages = []
    for msg in appeal.user_messages:
        all_messages.append(("👤 Вы", msg.created_date, msg.message))
    for msg in appeal.admin_messages:
        all_messages.append(("🛠 Поддержка", msg.created_date, msg.admin_message))
    all_messages.sort(key=lambda x: x[1])
    history_text = "*📝 История переписки:*\n\n"
    for sender, time, text in all_messages:
        message_line = f"{sender} ({time.strftime('%H:%M')}):\n{text}\n\n"
        history_text += message_line
    full_text = main_text + "\n\n" + history_text
    if len(full_text) <= 4000:
        return [], full_text
    message_parts = []
    current_part = "*📝 История переписки:*\n\n"
    for sender, time, text in all_messages:
        message_line = f"{sender} ({time.strftime('%H:%M')}):\n{text}\n\n"
        if len(current_part) + len(message_line) > 4000:
            message_parts.append(current_part)
            current_part = f"*📄 Продолжение истории обращения #{appeal.appeal_id}:*\n\n{message_line}"
        else:
            current_part += message_line
    if current_part and current_part != "*📝 История переписки:*\n\n":
        message_parts.append(current_part)
    return message_parts, main_text


async def admin_appeal_split_messages(
    appeal, admin_name: str = None
) -> tuple[list[str], str]:
    if not appeal:
        return [], "❌ Обращение не найдено"
    priority_dict = {
        "critical": "🚨 КРИТИЧЕСКИЙ",
        "high": "🔺 Высокий",
        "normal": "🔸 Обычный",
        "low": "🔹 Низкий",
    }
    user_info = f"👤 {appeal.user.user_first_name}"
    if appeal.user.username:
        user_info += f" (@{appeal.user.username})"
    main_text = f"""📨 *Обращение #{appeal.appeal_id}*
{status_dict.get(appeal.status, appeal.status)}
🎯 Приоритет: {priority_dict.get(appeal.priority, appeal.priority)}
{user_info}
📞 TG ID: `{appeal.telegram_id}`
📅 Создано: {appeal.created_date.strftime("%d.%m.%Y %H:%M")}
"""
    admin_info = f"Администратор {admin_name.capitalize()}"
    main_text += f"{admin_info}\n"
    if not appeal.user_messages and not appeal.admin_messages:
        return [], main_text + "\n\n📭 *Пока нет сообщений*"
    all_messages = []
    for msg in appeal.user_messages:
        all_messages.append(
            {
                "type": "user",
                "sender": "👤 Пользователь",
                "time": msg.created_date,
                "text": msg.message,
            }
        )
    for msg in appeal.admin_messages:
        sender_name = "🛠 Поддержка"
        if msg.admin and admin_name and msg.admin.name == admin_name:
            sender_name = f"👨‍💻 {msg.admin.name} (Вы)"
        elif msg.admin:
            sender_name = f"👨‍💻 {msg.admin.name}"
        all_messages.append(
            {
                "type": "admin",
                "sender": sender_name,
                "time": msg.created_date,
                "text": msg.admin_message,
            }
        )
    all_messages.sort(key=lambda x: x["time"])
    history_text = "*📝 История переписки:*\n\n"
    for msg in all_messages:
        message_line = (
            f"{msg['sender']} ({msg['time'].strftime('%H:%M')}):\n{msg['text']}\n\n"
        )
        history_text += message_line
    full_text = main_text + "\n\n" + history_text
    if len(full_text) <= 4000:
        return [], full_text
    message_parts = []
    current_part = "*📝 История переписки:*\n\n"
    for msg in all_messages:
        message_line = (
            f"{msg['sender']} ({msg['time'].strftime('%H:%M')}):\n{msg['text']}\n\n"
        )
        if len(current_part) + len(message_line) > 4000:
            message_parts.append(current_part)
            current_part = f"*📄 Продолжение истории обращения #{appeal.appeal_id}:*\n\n{message_line}"
        else:
            current_part += message_line
    if current_part and current_part != "*📝 История переписки:*\n\n":
        message_parts.append(current_part)
    return message_parts, main_text


async def admin_message_rules() -> str:
    return """
💡 *ПРАВИЛА ОБЩЕНИЯ С ПОЛЬЗОВАТЕЛЯМИ*

📝 *Основные принципы:*
• Будьте вежливы и профессиональны
• Обращайтесь к пользователю по имени
• Сообщайте информацию четко и понятно
• Сохраняйте спокойный тон даже в сложных ситуациях

⏰ *Сроки ответа:*
• Стандартные обращения - ответ в течение 24 часов
• Критические проблемы - ответ в течение 1-2 часов
• Высокий приоритет - ответ в течение 4-6 часов

🔒 *Безопасность:*
• Не запрашивайте пароли и платежные данные
• Не переходите по подозрительным ссылкам от пользователей
• Не разглашайте личную информацию других пользователей
• Сообщайте о подозрительных действиях старшему админу

📋 *Формат ответов:*
• Приветствие и обращение по имени
• Четкий ответ на вопрос
• Предложение дальнейшей помощи
• Подпись (ваше имя)

🚫 *Запрещено:*
• Грубость и неуважительное общение
• Использование ненормативной лексики
• Оскорбления пользователей
• Обсуждение внутренней информации компании

📞 *Эскалация проблем:*
• Сложные технические вопросы → передайте старшему админу
• Жалобы на других админов → немедленно старшему админу
• Подозрения на мошенничество → срочно старшему админу

*Теперь вы можете отправить ответ пользователю. Ваше сообщение будет доставлено сразу после отправки.*
"""


GENRES = {
    "fantasy": "Фэнтази",
    "horror": "Ужасы",
    "science_fiction": "Научная Фантастика",
    "detective": "Детектив",
    "classic": "Классическая литература",
    "poetry": "Поэзия",
}


GENRES = {
    "fantasy": "Фэнтази",
    "horror": "Ужасы",
    "science_fiction": "Научная Фантастика",
    "detective": "Детектив",
    "classic": "Классическая литература",
    "poetry": "Поэзия",
}


async def admin_all_statistic_text(stats: dict) -> str:
    # Текущая дата и время
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Финансы
    realized_revenue_today = stats.get("realized_revenue_today", 0)
    realized_revenue_month = stats.get("realized_revenue_month", 0)
    realized_revenue_total = stats.get("realized_revenue_total", 0)
    expected_revenue_today = stats.get("expected_revenue_today", 0)
    expected_revenue_month = stats.get("expected_revenue_month", 0)
    expected_revenue_total = stats.get("expected_revenue_total", 0)

    # Заказы
    orders_today = stats.get("orders_today", 0)
    orders_month = stats.get("orders_month", 0)
    orders_total = stats.get("orders_total", 0)
    delivering_orders = stats.get("delivering_orders", 0)
    processing_orders = stats.get("processing_orders", 0)
    completed_orders = stats.get("completed_orders", 0)
    cancelled_today = stats.get("cancelled_today", 0)
    cancelled_month = stats.get("cancelled_month", 0)
    cancelled_total = stats.get("cancelled_total", 0)

    # Пользователи
    total_users = stats.get("total_users", 0)
    total_admins = stats.get("total_admins", 0)

    # Книги
    total_books = stats.get("total_books", 0)
    out_of_stock_books = stats.get("out_of_stock_books", 0)

    # Обращения
    active_appeals = stats.get("active_appeals", 0)
    critical_appeals = stats.get("critical_appeals", 0)

    # Админы по ролям
    admins_by_role = stats.get("admins_by_role", {})
    admins_role_text = ""
    for role, count in admins_by_role.items():
        admins_role_text += f"    • {role}: {count}\n"

    # Книги по жанрам
    books_by_genre_raw = stats.get("books_by_genre", {})
    books_genre_text = ""

    for genre_en, count in books_by_genre_raw.items():
        genre_ru = GENRES.get(genre_en, genre_en)
        books_genre_text += f"    • {genre_ru}: {count}\n"

    text = f"""<b>📊 Общая статистика магазина</b>
<i>Обновлено: {current_time}</i>

<b>💰 Финансы:</b>
    • Реализованная выручка:
      - Сегодня: {realized_revenue_today} руб.
      - За месяц: {realized_revenue_month} руб.
      - Всего: {realized_revenue_total} руб.
    
    • Ожидаемая выручка (в процессе):
      - Сегодня: {expected_revenue_today} руб.
      - За месяц: {expected_revenue_month} руб.
      - Всего: {expected_revenue_total} руб.

<b>📦 Заказы:</b>
    • Сегодня: {orders_today}
    • За месяц: {orders_month}
    • Всего: {orders_total}
    • В обработке: {processing_orders}
    • В доставке: {delivering_orders}
    • Доставлено: {completed_orders}
    • Отмены сегодня: {cancelled_today}
    • Отмены за месяц: {cancelled_month}
    • Всего отмен: {cancelled_total}

<b>👥 Пользователи:</b>
    • Всего пользователей: {total_users}
    • Всего администраторов: {total_admins}
    • По ролям:
{admins_role_text if admins_role_text else "    • Нет данных"}

<b>📚 Книги:</b>
    • Всего книг: {total_books}
    • Закончилось: {out_of_stock_books}
    • По жанрам:
{books_genre_text if books_genre_text else "    • Нет данных"}

<b>🆘 Обращения в поддержку:</b>
    • Активные обращения: {active_appeals}
    • Критические обращения: {critical_appeals if critical_appeals > 0 else "Нет критических обращений"}"""
    return text


async def admin_format_order_details(order_details: dict) -> str:
    order_id = order_details.get("order_id")
    total_price = order_details.get("total_price", 0)
    created_date = order_details.get("created_date")
    status = order_details.get("status", "Неизвестен")
    user_info = order_details.get("user", {})
    address_info = order_details.get("address", {})
    books = order_details.get("books", [])
    if isinstance(created_date, datetime):
        date_str = created_date.strftime("%d.%m.%Y %H:%M")
    else:
        date_str = "дата неизв."
    username = user_info.get("username", "Не указан")
    first_name = user_info.get("first_name", "Не указано")
    telegram_id = user_info.get("telegram_id", "Не указан")
    address_parts = []
    if address_info.get("city"):
        address_parts.append(f"🏙 {address_info['city']}")
    if address_info.get("street"):
        address_parts.append(f"улица {address_info['street']}")
    if address_info.get("house"):
        address_parts.append(f"д. {address_info['house']}")
    if address_info.get("apartment"):
        address_parts.append(f"кв. {address_info['apartment']}")
    address_text = ", ".join(address_parts) if address_parts else "Не указан"
    books_text = ""
    total_items = 0
    for i, book in enumerate(books, 1):
        title = book.get("title", "Неизвестная книга")
        price = book.get("price", 0)
        quantity = book.get("quantity", 1)
        total_items += quantity
        books_text += f"{i}. {title}\n"
        books_text += f"   └ {quantity} шт. × {price}₽ = {quantity * price}₽\n"
    text = f"""<b>📦 Заказ #{order_id}</b>

<b>📊 Общая информация:</b>
├ ID заказа: <code>{order_id}</code>
├ Статус: {status}
├ Общая сумма: <b>{total_price}₽</b>
├ Количество позиций: {len(books)}
├ Общее количество товаров: {total_items}
└ Дата создания: {date_str}

<b>👤 Информация о покупателе:</b>
├ Имя: {first_name}
├ Username: @{username}
└ Telegram ID: <code>{telegram_id}</code>

<b>🏠 Адрес доставки:</b>
├ Адрес: {address_text}
├ Получатель: {address_info.get("name", "Не указан")}
├ Телефон: {address_info.get("phone", "Не указан")}
└ Комментарий: {address_info.get("comment", "Нет комментария")}

<b>📚 Состав заказа:</b>
{books_text if books_text else "   └ Нет информации о товарах"}"""
    return text


def admin_order_statistic(stats: dict) -> str:
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    orders_today = stats.get("orders_today", 0)
    orders_month = stats.get("orders_month", 0)
    orders_total = stats.get("orders_total", 0)
    delivering_orders = stats.get("delivering_orders", 0)
    processing_orders = stats.get("processing_orders", 0)
    completed_orders = stats.get("completed_orders", 0)
    cancelled_today = stats.get("cancelled_today", 0)
    cancelled_month = stats.get("cancelled_month", 0)
    cancelled_total = stats.get("cancelled_total", 0)

    text = f"""<b>🛒 УПРАВЛЕНИЕ ЗАКАЗАМИ</b>
<i>Обновлено: {current_time}</i>

<b>📦 Статистика заказов:</b>
    • Сегодня: {orders_today}
    • За месяц: {orders_month}
    • Всего: {orders_total}
    • В обработке: {processing_orders}
    • В доставке: {delivering_orders}
    • Доставлено: {completed_orders}
    • Отмены сегодня: {cancelled_today}
    • Отмены за месяц: {cancelled_month}
    • Всего отмен: {cancelled_total}

<b>Выберите действие:</b>"""

    return text


async def admin_personal_support_statistic(statistic_data: dict) -> str:
    total_appeals = statistic_data.get("total_appeals", 0)
    appeals_today = statistic_data.get("appeals_today", 0)
    new_appeals_today = statistic_data.get("new_appeals_today", 0)
    in_work_today = statistic_data.get("in_work_today", 0)
    closed_today_total = statistic_data.get("closed_today_total", 0)
    critical_appeals = statistic_data.get("critical_appeals", 0)
    high_priority_appeals = statistic_data.get("high_priority_appeals", 0)
    admin_name = statistic_data.get("admin_name", "Администратор")
    admin_active_appeals = statistic_data.get("admin_active_appeals", 0)
    admin_closed_appeals = statistic_data.get("admin_closed_appeals", 0)
    admin_responses_today = statistic_data.get("admin_responses_today", 0)
    admin_overdue_appeals = statistic_data.get("admin_overdue_appeals", 0)
    priority_msg = []
    if critical_appeals > 0:
        priority_msg.append(f"🚨 Критические: {critical_appeals}")
    if high_priority_appeals > 0:
        priority_msg.append(f"🔺 Высокие: {high_priority_appeals}")

    priority_text = (
        "\n".join(priority_msg)
        if priority_msg
        else "✅ Нет активных обращений с высоким приоритетом"
    )
    overdue_msg = ""
    if admin_overdue_appeals > 0:
        overdue_msg = f"⏰ Просрочено ответов: {admin_overdue_appeals}\n"

    return f"""
📊 СТАТИСТИКА ПОДДЕРЖКИ
👤 {admin_name}
📅 {statistic_data["stats_date"]} {statistic_data["generated_at"]}

{priority_text}
{overdue_msg}
🎯 ВАША РАБОТА:
• В работе: {admin_active_appeals} / 10 
• Закрытые вами: {admin_closed_appeals}
• Ответов сегодня: {admin_responses_today}

📈 ОБЩАЯ СТАТИСТИКА СИСТЕМЫ:
• Обращений сегодня: {appeals_today}
  ├─ Новые: {new_appeals_today}
  ├─ В работе: {in_work_today}
  └─ Закрыто: {closed_today_total}
• Всего обращений: {total_appeals}
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
