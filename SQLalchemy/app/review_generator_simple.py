# review_generator_simple.py

import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Review, Book, User
from review_templates import REVIEW_TEMPLATES


def generate_review(rating: int):
    """Генерация одного отзыва на основе рейтинга"""
    if rating >= 4:
        pool = REVIEW_TEMPLATES["positive"]
    elif rating == 3:
        pool = REVIEW_TEMPLATES["neutral"]
    else:
        pool = REVIEW_TEMPLATES["negative"]

    review = random.choice(pool)
    return review["title"], review["body"]


async def generate_reviews(session: AsyncSession):
    """Простая генерация отзывов для всех книг"""

    # Получаем все книги
    book_stmt = select(Book.book_id)
    book_result = await session.execute(book_stmt)
    book_ids = [row[0] for row in book_result.fetchall()]

    # Получаем всех пользователей
    user_stmt = select(User.telegram_id)
    user_result = await session.execute(user_stmt)
    user_ids = [row[0] for row in user_result.fetchall()]

    if not book_ids or not user_ids:
        print("Нет книг или пользователей")
        return

    reviews = []

    for book_id in book_ids:
        # Генерируем 5-8 отзывов на книгу
        for _ in range(random.randint(5, 8)):
            user_id = random.choice(user_ids)

            # Генерируем рейтинг
            rand = random.random()
            if rand <= 0.40:  # 40% - 5
                rating = 5
            elif rand <= 0.70:  # 30% - 4
                rating = 4
            elif rand <= 0.90:  # 20% - 3
                rating = 3
            elif rand <= 0.95:  # 5% - 2
                rating = 2
            else:  # 5% - 1
                rating = 1

            title, body = generate_review(rating)

            # Случайная дата за последний год
            random_days = random.randint(0, 365)
            random_hours = random.randint(0, 23)
            created_at = datetime.now() - timedelta(
                days=random_days, hours=random_hours
            )

            review = Review(
                book_id=book_id,
                telegram_id=user_id,
                review_rating=rating,
                review_title=title,
                review_body=body,
                finished=True,
                published=True,
                created_at=created_at,
                updated_at=created_at,
            )

            reviews.append(review)

    # Добавляем все отзывы
    session.add_all(reviews)
    await session.commit()

    print(f"✅ Сгенерировано {len(reviews)} отзывов для {len(book_ids)} книг")
