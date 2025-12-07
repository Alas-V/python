from database import AsyncSessionLocal
from models import (
    Author,
    Book,
    User,
    Review,
    BookStatus,
    OrderStatus,
    AppealStatus,
    BookGenre,
    Cart,
    CartItem,
    UserAddress,
    OrderData,
    AdminMessage,
    UserMessage,
    SupportAppeal,
    Admin,
    AdminPermission,
    PriorityStatus,
    AdminRole,
)
from faker import Faker
import random
from datetime import datetime, timedelta
from sqlalchemy import case, select, text, func, and_, update, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import Dict, Any, List, Tuple
import math
from typing import Optional
from authors import REAL_AUTHORS
from books import REAL_BOOKS


fake = Faker("ru_RU")


order_type_to_admin_orders_dict = {
    "new": OrderStatus.PROCESSING,
    "delivering": OrderStatus.DELIVERING,
    "completed": OrderStatus.COMPLETED,
    "canceled": OrderStatus.CANCELLED,
}

admin_role_dict = {
    "superadmin": AdminRole.SUPER_ADMIN,
    "admin": AdminRole.ADMIN,
    "manager": AdminRole.MANAGER,
    "moderator": AdminRole.MODERATOR,
    "deleted": AdminRole.DELETED,
    "new": AdminRole.NEW,
}


class AuthorQueries:
    @staticmethod
    async def add_author():
        async with AsyncSessionLocal() as session:
            author = Author(author_name="Rick Ruben", author_country="USA")
            author_se = Author(author_name="Dante Alighieri", author_country="Italy")
            book = Book(
                book_title="The Creative Act: A Way of Being",
                book_year=2023,
                author_id=2,
                book_price=1500,
                book_status=BookStatus.IN_STOCK,
                book_genre=BookGenre.CLASSIC,
                book_quantity=1,
            )
            session.add_all([author, author_se, book])
            await session.commit()

    @staticmethod
    async def get_author(id=None):
        async with AsyncSessionLocal() as session:
            if id:
                author = await session.get(Author, {"author_id": id})
                print(f"Имя - {author.author_name}, Страна - {author.author_country}")
                return
            result = await session.execute(select(Author))
            authors = result.scalars().all()
            for author in authors:
                print(
                    f"Имя - {author.author_name}, Страна - {author.author_country}, Книги автора - {author.author_books}"
                )
            return result

    @staticmethod
    async def get_author_with_books(author_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            stmt = text("""
                SELECT 
                    a.author_id, a.author_name, a.author_country,
                    b.book_id, b.book_title, b.book_year, b.book_status
                FROM authors a
                LEFT JOIN books b USING(author_id)
                WHERE a.author_id = :author_id
            """)
            result = await session.execute(stmt, {"author_id": author_id})
            rows = result.all()
            author_data = {
                "id": rows[0].author_id,
                "name": rows[0].author_name,
                "country": rows[0].author_country,
                "books": [],
            }
            for row in rows:
                if row.book_id:
                    author_data["books"].append(
                        {
                            "id": row.book_id,
                            "title": row.book_title,
                            "year": row.book_year,
                            "status": row.book_status,
                        }
                    )
        print(author_data)

    @staticmethod
    async def made_author_get_id(author_name: str) -> int:
        async with AsyncSessionLocal() as session:
            author = Author(
                author_name=author_name,
            )
            session.add(author)
            await session.flush()
            author_id = author.author_id
            await session.commit()
            return author_id

    @staticmethod
    async def get_author_data(author_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Author)
                .options(selectinload(Author.author_books))
                .where(Author.author_id == author_id)
            )
            author = result.scalar_one_or_none()
            if author:
                return {
                    "author_name": author.author_name,
                    "author_country": author.author_country,
                    "author_add_date": author.author_add_date,
                }
            return {}

    @staticmethod
    async def add_data_to_column(author_id: int, value: str, column: str):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Author)
                .where(Author.author_id == author_id)
                .values({column: value})
            )
            await session.flush()
            await session.commit()

    @staticmethod
    async def check_author_completion(author_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Author.author_name,
                    Author.author_country,
                ).where(Author.author_id == author_id)
            )
            data = result.first()
            if not data:
                return False
            name, country = data
            is_complete = all([name, country])
            return is_complete

    @staticmethod
    async def delete_author(author_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            author = await session.scalar(
                select(Author).where(Author.author_id == author_id)
            )
            await session.delete(author)
            await session.commit()
            return True

    @staticmethod
    async def get_book_author_id(book_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Book.author_id).where(Book.book_id == book_id)
            )
            author_id = result.scalar_one_or_none()
            return author_id

    @staticmethod
    async def assigned_new_author_to_book(new_author_id: int, book_id: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Book)
                .where(Book.book_id == book_id)
                .values({"author_id": new_author_id})
            )
            await session.flush()
            await session.commit()


class BookQueries:
    @staticmethod
    async def get_book(book_id: int):
        async with AsyncSessionLocal() as session:
            book = await session.get(Book, book_id)
            print(
                f"Название - {book.book_title}, Год - {book.book_year}, Цена - {book.book_price}\n"
            )

    # @staticmethod
    # async def select_avg_book_price():
    #     async with AsyncSessionLocal() as session:
    #         query = (
    #             select(
    #                 Author.author_name,
    #                 func.avg(Book.book_price).label("avg_book_price"),
    #             )
    #             .select_from(Book)
    #             .where(
    #                 and_(Book.book_year > 2000),
    #                 Book.book_status == "available",
    #             )
    #             .join(Author, Book.author_id == Author.author_id)
    #             .group_by(Author.author_name)
    #             .order_by(func.avg(Book.book_price).desc())
    #             .limit(5)
    #         )
    #         result = await session.execute(query)
    #         for author, price in result:
    #             rounded = round(price, 2)
    #             print(f"Автор - {author}, Средняя цена книг - {rounded}")

    # @staticmethod
    # async def get_avg_price():
    #     async with AsyncSessionLocal() as session:
    #         query = select(func.avg(Book.book_price))
    #         result = await session.execute(query)
    #         print(f"\nСредняя цена всех книг - {round(result.scalar(), 2)}")

    @staticmethod
    async def get_book_by_genre(genre: str):
        async with AsyncSessionLocal() as session:
            query = (
                select(
                    Book.book_id,
                    Book.book_title,
                    Book.book_on_sale,
                    Book.sale_value,
                    func.avg(Review.review_rating).label("book_rating"),
                )
                .select_from(Book)
                .outerjoin(Review)
                .where(and_(Book.book_genre == genre, Book.book_in_stock))
                .group_by(Book.book_id, Book.book_title)
                .order_by(Book.sale_value.desc(), Book.book_title)
            )
            result = await session.execute(query)
            return result.all()

    @staticmethod
    async def get_book_info(book_id):
        async with AsyncSessionLocal() as session:
            book_id_int = int(book_id)
            query = (
                select(
                    Book.book_id,
                    Book.book_title,
                    Book.book_year,
                    Book.book_quantity,
                    Book.book_price,
                    Book.book_genre,
                    Book.book_on_sale,
                    Book.sale_value,
                    Author.author_name,
                    Author.author_country,
                    func.avg(Review.review_rating).label("book_rating"),
                    func.count(Review.review_id).label("reviews_count"),
                )
                .select_from(Book)
                .join(Author, Book.author_id == Author.author_id, isouter=True)
                .join(
                    Review,
                    and_(Review.book_id == Book.book_id, Review.published),
                    isouter=True,
                )
                .where(Book.book_id == book_id_int)
                .group_by(
                    Book.book_id,
                    Author.author_id,
                )
            )
            result = await session.execute(query)
            book_data = result.mappings().first()
            if book_data and book_data["book_rating"] is None:
                book_data = dict(book_data)
                book_data["book_rating"] = 0.0
                book_data["reviews_count"] = 0

            return book_data

    @staticmethod
    async def get_book_reviews(book_id):
        async with AsyncSessionLocal() as session:
            book_id_int = int(book_id)
            book_query = (
                select(
                    Book.book_id,
                    Book.book_title,
                    Author.author_name,
                    func.avg(Review.review_rating).label("avg_rating"),
                    func.count(Review.review_id).label("reviews_count"),
                )
                .select_from(Book)
                .join(Author, Book.author_id == Author.author_id, isouter=True)
                .join(
                    Review,
                    and_(Review.book_id == Book.book_id, Review.published),
                    isouter=True,
                )  # OUTER JOIN
                .where(Book.book_id == book_id_int)
                .group_by(Book.book_id, Book.book_title, Author.author_name)
            )
            book_result = await session.execute(book_query)
            book_info = book_result.mappings().first()
            if book_info and book_info["avg_rating"] is None:
                book_info = dict(book_info)
                book_info["avg_rating"] = 0.0
                book_info["reviews_count"] = 0
            reviews_query = (
                select(
                    Review.review_id,
                    Review.review_rating,
                    Review.review_title,
                    Review.review_body,
                )
                .join(User, Review.telegram_id == User.telegram_id, isouter=True)
                .where(and_(Review.book_id == book_id_int, Review.published))
            )
            reviews_result = await session.execute(reviews_query)
            reviews = reviews_result.mappings().all()
            return {"book_info": book_info, "reviews": reviews}

    @staticmethod
    async def full_book_review(review_id):
        async with AsyncSessionLocal() as session:
            stmt = select(
                Review.review_rating,
                Review.review_title,
                Review.review_body,
                Review.created_at,
                Review.telegram_id,
            ).where(Review.review_id == review_id)
            reviews_result = await session.execute(stmt)
            reviews = reviews_result.mappings().first()
            return reviews

    @staticmethod
    async def decrease_book_value(book_data):
        async with AsyncSessionLocal() as session:
            for book in book_data:
                book_id = book.get("book_id")
                quantity_to_decrease = book.get("quantity")
                await session.execute(
                    update(Book)
                    .where(Book.book_id == book_id)
                    .values(
                        book_quantity=Book.book_quantity - quantity_to_decrease,
                        book_in_stock=case(
                            (Book.book_quantity - quantity_to_decrease > 0, True),
                            else_=False,
                        ),
                    )
                )
            await session.commit()

    @staticmethod
    async def check_book_availability(book_id: int, telegram_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            book_result = await session.execute(
                select(Book.book_quantity, Book.book_title, Book.book_in_stock).where(
                    Book.book_id == book_id
                )
            )
            book_info = book_result.first()
            if not book_info:
                return {"available": False, "message": "Книга не найдена"}
            available_quantity, book_title, in_stock = book_info
            if not in_stock or available_quantity <= 0:
                return {
                    "available": False,
                    "message": f"Книга '{book_title}' закончилась на складе",
                }
            cart_result = await session.execute(
                select(CartItem.quantity)
                .join(Cart)
                .where(
                    and_(Cart.telegram_id == telegram_id, CartItem.book_id == book_id)
                )
            )
            current_in_cart = cart_result.scalar_one_or_none() or 0
            if current_in_cart + 1 > available_quantity:
                return {
                    "available": False,
                    "message": (
                        f"📚 К сожалению, на нашем складе только {available_quantity} экземпляров книги «{book_title}»\n\n"
                        f"🛒 У вас уже в корзине: {current_in_cart} шт.\n"
                    ),
                }
            return {"available": True, "book_title": book_title}

    @staticmethod
    async def more_than_zero_books(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Book.book_quantity).where(Book.book_id == book_id)
            )
            quantity = result.scalar_one_or_none()
            return quantity is not None and quantity > 0

    @staticmethod
    async def check_book_done(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Book).where(Book.book_id == book_id))
            book = result.scalar_one_or_none()
            if not book:
                return False
            required_fields = [
                book.book_title,
                book.book_year,
                book.author_id,
                book.book_price,
                book.book_genre,
                book.book_quantity,
            ]
            return all(required_fields)

    @staticmethod
    async def check_books_availability(book_data) -> tuple[bool, list]:
        async with AsyncSessionLocal() as session:
            book_ids = [book["book_id"] for book in book_data]
            result = await session.execute(
                select(Book.book_id, Book.book_quantity, Book.book_title).where(
                    Book.book_id.in_(book_ids)
                )
            )
            books_in_db = result.all()
            db_books_map = {
                book_id: (quantity, title) for book_id, quantity, title in books_in_db
            }
            insufficient_books = []
            all_available = True
            for book in book_data:
                book_id = book["book_id"]
                required_quantity = book["quantity"]
                if book_id not in db_books_map:
                    insufficient_books.append(f"❌ Книга ID {book_id} не найдена")
                    all_available = False
                    continue
                current_quantity, title = db_books_map[book_id]
                if current_quantity < required_quantity:
                    insufficient_books.append(
                        f"❌ {title}: нужно {required_quantity}, есть {current_quantity}"
                    )
                    all_available = False
            return all_available, insufficient_books

    @staticmethod
    async def add_books_back_when_canceled_order(books: list):
        async with AsyncSessionLocal() as session:
            for book_id, quantity in books:
                result = await session.execute(
                    select(Book.book_quantity).where(Book.book_id == book_id)
                )
                current_quantity = result.scalar_one_or_none()
                if current_quantity is not None:
                    await session.execute(
                        update(Book)
                        .where(Book.book_id == book_id)
                        .values(book_quantity=Book.book_quantity + quantity)
                    )
                await session.flush()
            await session.commit()

    @staticmethod
    async def has_cover(book_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Book.book_photo_id).where(Book.book_id == book_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_books_for_admin() -> dict:
        async with AsyncSessionLocal() as session:
            try:
                total_books_result = await session.execute(
                    select(func.count(Book.book_id))
                )
                total_books = total_books_result.scalar()
                status_count_result = await session.execute(
                    select(Book.book_status, func.count(Book.book_id)).group_by(
                        Book.book_status
                    )
                )
                status_counts = dict(status_count_result.all())
                genre_count_result = await session.execute(
                    select(Book.book_genre, func.count(Book.book_id)).group_by(
                        Book.book_genre
                    )
                )
                genre_counts = dict(genre_count_result.all())
                total_quantity_result = await session.execute(
                    select(func.sum(Book.book_quantity))
                )
                total_quantity = total_quantity_result.scalar() or 0
                on_sale_count_result = await session.execute(
                    select(func.count(Book.book_id)).where(Book.book_on_sale)
                )
                on_sale_count = on_sale_count_result.scalar()
                avg_price_result = await session.execute(
                    select(func.avg(Book.book_price))
                )
                avg_price = avg_price_result.scalar() or 0
                low_stock_result = await session.execute(
                    select(func.count(Book.book_id)).where(Book.book_quantity < 10)
                )
                low_stock_count = low_stock_result.scalar()
                recent_books_result = await session.execute(
                    select(Book).order_by(Book.book_add_date.desc()).limit(5)
                )
                recent_books = recent_books_result.scalars().all()
                return {
                    "total_books": total_books,
                    "status_counts": status_counts,
                    "genre_counts": genre_counts,
                    "total_quantity": total_quantity,
                    "on_sale_count": on_sale_count,
                    "avg_price": float(avg_price) if avg_price else 0,
                    "low_stock_count": low_stock_count,
                    "recent_books": [
                        {
                            "book_id": book.book_id,
                            "title": book.book_title,
                            "price": book.book_price,
                            "quantity": book.book_quantity,
                            "status": book.book_status,
                            "genre": book.book_genre,
                        }
                        for book in recent_books
                    ],
                }
            except Exception as e:
                print(f"Error in get_books_for_admin: {e}")
                return {}

    @staticmethod
    async def made_book_with_admin_id_get_book_id(author_id: int) -> int:
        async with AsyncSessionLocal() as session:
            book = Book(author_id=author_id)
            session.add(book)
            await session.commit()
            await session.refresh(book)
            return book.book_id

    @staticmethod
    async def get_book_info_for_new(book_id):
        async with AsyncSessionLocal() as session:
            query = (
                select(
                    Book.book_id,
                    Book.book_title,
                    Book.book_year,
                    Book.book_quantity,
                    Book.book_price,
                    Book.book_genre,
                    Book.book_on_sale,
                    Book.sale_value,
                    Author.author_name,
                    Author.author_country,
                )
                .join(Author, Book.author_id == Author.author_id, isouter=True)
                .where(Book.book_id == book_id)
            )
            result = await session.execute(query)
            return result.mappings().first()

    @staticmethod
    async def get_book_sale_info(book_id: int):
        async with AsyncSessionLocal() as session:
            query = select(
                Book.book_id,
                Book.book_title,
                Book.book_price,
                Book.book_on_sale,
                Book.sale_value,
            ).where(Book.book_id == book_id)
            result = await session.execute(query)
            return result.mappings().first()

    @staticmethod
    async def get_book_price(book_id: int) -> Optional[int]:
        async with AsyncSessionLocal() as session:
            query = select(Book.book_price).where(Book.book_id == book_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def remove_book_sale(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(Book).where(Book.book_id == book_id)
                result = await session.execute(stmt)
                book = result.scalar_one_or_none()
                if not book:
                    return False
                book.book_on_sale = False
                book.sale_value = None
                book.updated_at = datetime.now()
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"Error removing book sale: {e}")
                return False

    @staticmethod
    async def update_book_sale(book_id: int, sale_percent: int) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                sale_value = sale_percent / 100
                stmt = select(Book).where(Book.book_id == book_id)
                result = await session.execute(stmt)
                book = result.scalar_one_or_none()
                if not book:
                    return False
                book.book_on_sale = True
                book.sale_value = sale_value
                book.updated_at = datetime.now()
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"Error updating book sale: {e}")
                return False

    @staticmethod
    async def has_sale(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            query = await session.execute(
                select(Book.book_on_sale).where(Book.book_id == book_id)
            )
            return query.scalar_one_or_none()

    @staticmethod
    async def search_books_by_title_for_admin(
        title_query: str, limit: int = 20
    ) -> List[Dict]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    select(Book.book_id, Book.book_title, Author.author_name)
                    .join(Author, Book.author_id == Author.author_id)
                    .where(Book.book_title.ilike(f"%{title_query}%"))
                    .order_by(Book.book_title)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                rows = result.fetchall()
                books_list = []
                for row in rows:
                    books_list.append(
                        {
                            "book_id": row.book_id,
                            "book_title": row.book_title,
                            "author_name": row.author_name,
                        }
                    )
                return books_list
            except Exception as e:
                print(f"Error in search_books_by_title_for_admin: {e}")
                return []

    @staticmethod
    async def search_books_by_title_with_pagination(
        title_query: str, offset: int = 0, limit: int = 10
    ) -> Tuple[List[Dict], int]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    select(Book)
                    .options(selectinload(Book.author))
                    .where(Book.book_title.ilike(f"%{title_query}%"))
                    .order_by(Book.book_title)
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                books = result.scalars().all()
                books_list = []
                for book in books:
                    books_list.append(
                        {
                            "book_id": book.book_id,
                            "book_title": book.book_title,
                            "author_name": book.author.author_name
                            if book.author
                            else None,
                        }
                    )
                count_stmt = select(func.count(Book.book_id)).where(
                    Book.book_title.ilike(f"%{title_query}%")
                )
                total_count = await session.scalar(count_stmt)
                return books_list, total_count
            except Exception as e:
                print(f"Error in search_books_by_title_with_pagination: {e}")
                return [], 0

    @staticmethod
    async def search_books_by_title(title_query: str, limit: int = 20) -> List[Dict]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    select(Book)
                    .options(selectinload(Book.author))
                    .where(Book.book_title.ilike(f"%{title_query}%"))
                    .order_by(Book.book_title)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                books = result.scalars().all()
                books_list = []
                for book in books:
                    books_list.append(
                        {
                            "book_id": book.book_id,
                            "book_title": book.book_title,
                            "author_name": book.author.author_name
                            if book.author
                            else None,
                            "book_price": book.book_price,
                            "book_in_stock": book.book_in_stock,
                        }
                    )
                return books_list
            except Exception as e:
                print(f"Error in search_books_by_title: {e}")
                return []

    @staticmethod
    async def get_books_not_in_stock(limit: int = 50) -> List[Dict]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    select(Book)
                    .options(selectinload(Book.author))
                    .where(or_(Book.book_in_stock == False, Book.book_quantity <= 0))
                    .order_by(Book.book_title)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                books = result.scalars().all()
                books_list = []
                for book in books:
                    books_list.append(
                        {
                            "book_id": book.book_id,
                            "book_title": book.book_title,
                            "author_name": book.author.author_name
                            if book.author
                            else None,
                            "book_price": book.book_price,
                            "book_quantity": book.book_quantity,
                            "book_in_stock": book.book_in_stock,
                        }
                    )
                return books_list
            except Exception as e:
                print(f"Error in get_books_not_in_stock: {e}")
                return []

    @staticmethod
    async def search_books_by_title_for_user(
        title_query: str, limit: int = 20
    ) -> List[Dict]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    select(Book)
                    .options(selectinload(Book.author))
                    .where(
                        and_(
                            Book.book_title.ilike(f"%{title_query}%"),
                            Book.book_in_stock == True,
                            Book.book_status == BookStatus.APPROVED,
                        )
                    )
                    .order_by(Book.book_title)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                books = result.scalars().all()
                books_list = []
                for book in books:
                    books_list.append(
                        {
                            "book_id": book.book_id,
                            "book_title": book.book_title,
                            "author_name": book.author.author_name
                            if book.author
                            else None,
                        }
                    )
                return books_list
            except Exception as e:
                print(f"Error in search_books_by_title_for_user: {e}")
                return []

    @staticmethod
    async def get_sale_genre(genre):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Book.book_id,
                    Book.book_title,
                    Book.book_on_sale,
                    Book.sale_value,
                    func.avg(Review.review_rating).label("book_rating"),
                )
                .where(
                    and_(
                        Book.book_genre == genre, Book.book_on_sale, Book.book_in_stock
                    )
                )
                .outerjoin(Review)
                .group_by(Book.book_id, Book.book_title)
                .order_by(Book.sale_value.desc(), Book.book_title)
            )
            return result.mappings().all()


class SaleQueries:
    @staticmethod
    async def add_on_sale(book_ids: list, sale_value: float):
        async with AsyncSessionLocal() as session:
            stmt = (
                update(Book)
                .where(Book.book_id.in_(book_ids))
                .values(book_on_sale=True, sale_value=sale_value)
                .execution_options(synchronize_session=False)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def out_of_sale(book_ids: list):
        async with AsyncSessionLocal() as session:
            stmt = (
                update(Book)
                .where(Book.book_id.in_(book_ids))
                .values(book_on_sale=False, sale_value=0)
                .execution_options(synchronize_session=False)
            )
            await session.execute(stmt)
            await session.commit()
            return True


class UserQueries:
    # @staticmethod
    # async def update_user(user_id: int, new_username: str):
    #     async with AsyncSessionLocal() as session:
    #         user = await session.get(User, user_id)
    #         user.username = new_username
    #         await session.commit()

    @staticmethod
    async def draft_reviews(telegram_id):
        async with AsyncSessionLocal() as session:
            has_draft = await session.execute(
                select(Review.review_id).where(
                    and_(Review.telegram_id == telegram_id, Review.published.is_(False))
                )
            )
            draft = has_draft.first()
            if draft:
                return True
            return False

    @staticmethod
    async def published_check(telegram_id):
        async with AsyncSessionLocal() as session:
            has_published = await session.execute(
                select(Review.review_id).where(
                    and_(Review.telegram_id == telegram_id, Review.published)
                )
            )
            published = has_published.first()
            if published:
                return True
            return False

    @staticmethod
    async def get_user_published_reviews(telegram_id):
        async with AsyncSessionLocal() as session:
            reviews_query = (
                select(
                    Review.review_id,
                    Review.review_rating,
                    Review.review_title,
                    Review.review_body,
                    Book.book_title,
                    Book.book_id,
                )
                .join(Book, Book.book_id == Review.book_id)
                .where(and_(Review.telegram_id == telegram_id, Review.published))
                .order_by(Review.updated_at)
            )
            reviews_result = await session.execute(reviews_query)
            reviews = reviews_result.mappings().all()
            return reviews

    @staticmethod
    async def get_user_draft(telegram_id):
        async with AsyncSessionLocal() as session:
            drafts = await session.execute(
                select(
                    Review.review_id,
                    Review.review_rating,
                    Review.review_title,
                    Review.review_body,
                    Book.book_title,
                    Book.book_id,
                )
                .join(Book, Book.book_id == Review.book_id)
                .where(
                    and_(Review.telegram_id == telegram_id, Review.published.is_(False))
                )
                .order_by(Review.updated_at)
            )
            reviews = drafts.mappings().all()
            return reviews

    @staticmethod
    async def get_user_balance(telegram_id) -> int:
        async with AsyncSessionLocal() as session:
            balance = int(
                await session.scalar(
                    select(User.user_balance).where(User.telegram_id == telegram_id)
                )
            )
            return balance

    @staticmethod
    async def get_user_if_exist(user_data: dict):
        async with AsyncSessionLocal() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_data["telegram_id"])
            )
            user = user.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_id=user_data["telegram_id"],
                    username=user_data["username"],
                    user_first_name=user_data["user_first_name"],
                )
                await session.flush()
                cart = Cart(telegram_id=user_data["telegram_id"])
                session.add_all([user, cart])
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def updata_user_balance(telegram_id, value):
        async with AsyncSessionLocal() as session:
            stmt = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(user_balance=value)
            )
            await session.execute(stmt)
            await session.commit()
            return True


class ReviewQueries:
    @staticmethod
    async def new_review(telegram_id: int, book_id: int):
        async with AsyncSessionLocal() as session:
            new_review = Review(
                book_id=book_id,
                review_rating=0,
                review_title=None,
                review_body=None,
                telegram_id=telegram_id,
                finished=False,
                published=False,
            )
            session.add(new_review)
            await session.flush()
            review_id = new_review.review_id
            await session.commit()
            return review_id

    @staticmethod
    async def check_review_finished(review_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Review.review_rating, Review.review_title, Review.review_body
                ).where(Review.review_id == review_id)
            )
            data = result.first()
            if not data:
                return False
            rating, title, body = data
            return all(
                [
                    rating is not None and rating > 0,
                    title is not None and title.strip() != "",
                    body is not None and body.strip() != "",
                ]
            )

    @staticmethod
    async def add_value_column(review_id: int, column, data):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Review)
                .where(Review.review_id == review_id)
                .values({column: data})
            )
            await session.commit()
            is_finished = await ReviewQueries.check_review_finished(review_id)
            return is_finished

    @staticmethod
    async def review_get_next_empty_field(review_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Review).where(Review.review_id == review_id)
            )
            review = result.scalar_one()
            if review.review_rating is None:
                return "rating"
            elif review.review_title is None:
                return "title"
            elif review.review_body is None:
                return "body"

    @staticmethod
    async def delete_review_sure(review_id, telegram_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Review).where(
                        and_(
                            Review.review_id == review_id,
                            Review.telegram_id == telegram_id,
                        )
                    )
                )
                review = result.scalar_one_or_none()
                if review:
                    await session.delete(review)
                    await session.commit()
                    return True
                return False
            except Exception as e:
                await session.rollback()
                return False

    @staticmethod
    async def review_exist(telegram_id: int, book_id: int):
        async with AsyncSessionLocal() as session:
            review = await session.execute(
                select(Review.review_id).where(
                    and_(Review.telegram_id == telegram_id, Review.book_id == book_id)
                )
            )
            result = review.scalar_one_or_none()
            return result

    @staticmethod
    async def check_review_completion(review_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Review.review_rating,
                    Review.review_title,
                    Review.review_body,
                ).where(Review.review_id == review_id)
            )
            data = result.first()
            if not data:
                return False
            rating, title, body = data
            is_complete = all([rating, body, title])
            return is_complete


class SupportQueries:
    @staticmethod
    async def check_if_exist(telegram_id):
        async with AsyncSessionLocal() as session:
            ticket = await session.execute(
                select(SupportAppeal).where(SupportAppeal.telegram_id == telegram_id)
            )
            result = ticket.first() is not None
            return result

    @staticmethod
    async def get_appeals_count(telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(SupportAppeal.appeal_id)).where(
                    SupportAppeal.telegram_id == telegram_id
                )
            )
            return result.scalar_one()

    @staticmethod
    async def get_small_appeals_paginated(
        telegram_id: int, page: int = 0, limit: int = 5
    ):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    SupportAppeal.appeal_id,
                    SupportAppeal.created_date,
                    SupportAppeal.status,
                )
                .where(SupportAppeal.telegram_id == telegram_id)
                .order_by(SupportAppeal.created_date.desc())
                .offset(page * limit)
                .limit(limit)
            )
            appeals = result.tuples().all()
            return appeals

    @staticmethod
    async def create_new_appeal(telegram_id: int):
        async with AsyncSessionLocal() as session:
            appeal = SupportAppeal(
                telegram_id=telegram_id,
                priority=PriorityStatus.NORMAL,
            )
            session.add(appeal)
            await session.flush()
            appeal_id = appeal.appeal_id
            await session.commit()
            return appeal_id

    @staticmethod
    async def can_create_appeal(telegram_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal.created_date)
                .where(SupportAppeal.telegram_id == telegram_id)
                .order_by(SupportAppeal.created_date.desc())
                .limit(1)
            )
            last_appeal = result.scalar_one_or_none()
            if not last_appeal:
                return True
            # return True  # DEBUG  no cooldown at all
            time_passed = datetime.utcnow() - last_appeal
            return time_passed.total_seconds() >= 3600

    @staticmethod
    async def get_cooldown_minutes(telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal.created_date)
                .where(SupportAppeal.telegram_id == telegram_id)
                .order_by(SupportAppeal.created_date.desc())
                .limit(1)
            )
            last_appeal = result.scalar_one_or_none()
            if not last_appeal:
                return 0
            time_passed = datetime.utcnow() - last_appeal
            remaining_seconds = 3600 - time_passed.total_seconds()
            if remaining_seconds <= 0:
                return 0
            return math.ceil(remaining_seconds / 60)

    @staticmethod
    async def message_cooldown(telegram_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserMessage.created_date)
                .where(UserMessage.telegram_id == telegram_id)
                .order_by(UserMessage.created_date.desc())
                .limit(1)
            )
            last_message = result.scalar_one_or_none()
            if not last_message:
                return True
            # return True  # DEBUG для дебага , убирает cooldown для пользовательских сообщений
            time_passed = datetime.utcnow() - last_message
            return time_passed.total_seconds() >= 120

    @staticmethod
    async def get_message_cooldown_seconds(telegram_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserMessage.created_date)
                .where(UserMessage.telegram_id == telegram_id)
                .order_by(UserMessage.created_date.desc())
                .limit(1)
            )
            last_message = result.scalar_one_or_none()
            if not last_message:
                return 0
            time_passed = datetime.utcnow() - last_message
            remaining_seconds = 120 - time_passed.total_seconds()
            if remaining_seconds <= 0:
                return 0
            return int(remaining_seconds)

    @staticmethod
    async def get_last_appeal_id(telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal.appeal_id)
                .where(SupportAppeal.telegram_id == telegram_id)
                .order_by(SupportAppeal.created_date.desc())
                .limit(1)
            )
            last_appeal_id = result.scalar_one()
            return last_appeal_id

    @staticmethod
    async def check_appeal_status(appeal_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal.status).where(SupportAppeal.appeal_id == appeal_id)
            )
            status = result.scalar_one_or_none()
            return status

    @staticmethod
    async def get_appeal_full(appeal_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .options(
                    selectinload(SupportAppeal.user_messages),
                    selectinload(SupportAppeal.admin_messages),
                )
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def new_user_message(telegram_id, appeal_id, message):
        async with AsyncSessionLocal() as session:
            new_message = UserMessage(
                telegram_id=telegram_id, message=message, appeal_id=appeal_id
            )
            session.add(new_message)
            await session.execute(
                update(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .values(admin_visit=False)
            )
            await session.commit()

    @staticmethod
    async def close_appeal(appeal_id: int, who_close: str) -> bool:
        async with AsyncSessionLocal() as session:
            if who_close == "user":
                new_status = AppealStatus.CLOSED_BY_USER
            elif who_close == "admin":
                new_status = AppealStatus.CLOSED_BY_ADMIN
            else:
                return False
            stmt = (
                update(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .values(status=new_status)
                .execution_options(synchronize_session=False)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def has_user_msg(appeal_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(UserMessage.message_id)).where(
                    UserMessage.appeal_id == appeal_id
                )
            )
            count = result.scalar()
            return count > 0

    @staticmethod
    async def create_admin_initiated_appeal(telegram_id: int, admin_id: int) -> int:
        async with AsyncSessionLocal() as session:
            appeal = SupportAppeal(
                telegram_id=telegram_id,
                assigned_admin_id=admin_id,
                status=AppealStatus.IN_WORK,
                priority=PriorityStatus.NORMAL,
                admin_initiative=True,
                admin_visit=True,
            )
            session.add(appeal)
            await session.flush()
            appeal_id = appeal.appeal_id
            await session.commit()
            return appeal_id


class OrderQueries:
    @staticmethod
    async def add_book_to_cart(telegram_id, book_id):
        async with AsyncSessionLocal() as session:
            cart = await session.execute(
                select(Cart).where(Cart.telegram_id == telegram_id)
            )
            cart = cart.scalar_one_or_none()
            book_price = await session.execute(
                select(Book.book_price, Book.book_on_sale, Book.sale_value).where(
                    Book.book_id == book_id
                )
            )
            book_price_info = book_price.mappings().first()
            full_price = float(book_price_info.get("book_price"))
            sale_value = float(book_price_info.get("sale_value", 0))
            new_price = round(full_price * (1 - sale_value), 2)
            if not cart:
                cart = Cart(
                    telegram_id=telegram_id,
                )
                session.add(cart)
                await session.commit()
                await session.refresh(cart)
            existing_item = await session.execute(
                select(CartItem).where(
                    and_(CartItem.cart_id == cart.cart_id, CartItem.book_id == book_id)
                )
            )
            existing_item = existing_item.scalars().first()
            if existing_item:
                existing_item.quantity += 1
            else:
                if book_price_info["book_on_sale"]:
                    cart_item = CartItem(
                        book_id=book_id,
                        cart_id=cart.cart_id,
                        quantity=1,
                        price=new_price,
                    )
                else:
                    cart_item = CartItem(
                        book_id=book_id,
                        cart_id=cart.cart_id,
                        quantity=1,
                        price=full_price,
                    )
                session.add(cart_item)
            await session.commit()
            return True

    @staticmethod
    async def get_cart_total(telegram_id: int):
        async with AsyncSessionLocal() as session:
            cart_id = await session.execute(
                select(Cart.cart_id).where(Cart.telegram_id == telegram_id)
            )
            cart_id = cart_id.scalar()
            cart_items = await session.execute(
                select(CartItem.price, CartItem.quantity, CartItem.book_id).where(
                    CartItem.cart_id == cart_id
                )
            )
            total_price = 0
            books_in_cart = []
            for price, quantity, book_id in cart_items:
                total_price += price * quantity
                book_title = await session.scalar(
                    select(Book.book_title).where(Book.book_id == book_id)
                )
                books_in_cart.append(
                    {
                        "book_id": book_id,
                        "book": book_title,
                        "price": price,
                        "quantity": quantity,
                    }
                )
            return [total_price, books_in_cart]

    @staticmethod
    async def del_cart(telegram_id):
        async with AsyncSessionLocal() as session:
            cart = await session.scalar(
                select(Cart.cart_id).where(Cart.telegram_id == telegram_id)
            )
            cart_items = await session.scalar(
                select(CartItem).where(CartItem.cart_id == cart)
            )
            if cart_items:
                await session.delete(cart_items)
                await session.commit()
                return True, telegram_id
            return False, telegram_id

    @staticmethod
    async def delete_address_orm(address_id):
        async with AsyncSessionLocal() as session:
            address = await session.scalar(
                select(UserAddress).where(UserAddress.address_id == address_id)
            )
            await session.delete(address)
            await session.commit()
            return True

    @staticmethod
    async def update_info(telegram_id, address_id, column, data):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserAddress)
                .where(
                    and_(
                        UserAddress.telegram_id == telegram_id,
                        UserAddress.address_id == address_id,
                    )
                )
                .values({column: data})
            )
            await session.commit()
            is_complete = await OrderQueries.check_address_completion(
                address_id=int(address_id)
            )
            return is_complete

    @staticmethod
    async def get_user_address_data(telegram_id, address_id: int):
        async with AsyncSessionLocal() as session:
            order_data = await session.execute(
                select(
                    UserAddress.name,
                    UserAddress.phone,
                    UserAddress.city,
                    UserAddress.street,
                    UserAddress.house,
                    UserAddress.apartment,
                    UserAddress.comment,
                    UserAddress.is_complete,
                ).where(
                    and_(
                        UserAddress.telegram_id == telegram_id,
                        UserAddress.address_id == address_id,
                    )
                )
            )
            return order_data.first()

    @staticmethod
    async def get_next_empty_field(address_id: int, telegram_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserAddress).where(UserAddress.address_id == address_id)
            )
            address = result.scalar_one()
            if address.name is None:
                return "name"
            elif address.phone is None:
                return "phone"
            elif address.city is None:
                return "city"
            elif address.street is None:
                return "street"
            elif address.house is None:
                return "house"
            else:
                return None

    @staticmethod
    async def check_address_completion(address_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    UserAddress.name,
                    UserAddress.phone,
                    UserAddress.city,
                    UserAddress.street,
                    UserAddress.house,
                    UserAddress.is_complete,
                ).where(UserAddress.address_id == address_id)
            )
            data = result.first()
            if not data:
                return False
            name, phone, city, street, house, current_status = data
            is_complete = all([name, phone, city, street, house])
            return is_complete

    @staticmethod
    async def has_address(telegram_id):
        async with AsyncSessionLocal() as session:
            has_address = await session.execute(
                select(UserAddress.address_id).where(
                    UserAddress.telegram_id == telegram_id
                )
            )
            address = has_address.first()
            if address:
                return True
            return False

    @staticmethod
    async def get_address_small(telegram_id):
        async with AsyncSessionLocal() as session:
            addresses = await session.execute(
                select(
                    UserAddress.address_id,
                    UserAddress.city,
                    UserAddress.street,
                    UserAddress.house,
                )
                .where(UserAddress.telegram_id == telegram_id)
                .order_by(UserAddress.created_date.desc())
            )
            return addresses.mappings().all()

    @staticmethod
    async def add_address_get_id(telegram_id):
        async with AsyncSessionLocal() as session:
            new_address = UserAddress(
                telegram_id=telegram_id,
                name=None,
                phone=None,
                city=None,
                street=None,
                house=None,
                apartment=None,
                payment=None,
                comment=None,
                is_complete=False,
            )
            session.add(new_address)
            await session.flush()
            address_id = new_address.address_id
            await session.commit()
            return address_id

    @staticmethod
    async def made_order(telegram_id, address_id, price, cart_data):
        async with AsyncSessionLocal() as session:
            book_ids = []
            book_quants = []
            for book in cart_data:
                book_id = book.get("book_id")
                quant = book.get("quantity")
                book_ids.append(book_id)
                book_quants.append(quant)
            new_order = OrderData(
                address_id=address_id,
                telegram_id=telegram_id,
                price=price,
                book_id=book_ids,
                quantity=book_quants,
            )
            session.add(new_order)
            await session.flush()
            order_id = new_order.order_id
            await session.commit()
            return order_id

    @staticmethod
    async def get_user_orders(telegram_id, limit: int = 5, offset: int = 0):
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    OrderData.order_id,
                    OrderData.status,
                    OrderData.price,
                    OrderData.created_date,
                )
                .order_by(OrderData.created_date.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.mappings().all()

    @staticmethod
    async def get_user_orders_count(telegram_id: int):
        async with AsyncSessionLocal() as session:
            stmt = select(func.count()).where(OrderData.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar()

    @staticmethod
    async def get_order_details(order_id: int, telegram_id: int):
        async with AsyncSessionLocal() as session:
            order_stmt = (
                select(
                    OrderData.order_id,
                    OrderData.status,
                    OrderData.price,
                    OrderData.created_date,
                    OrderData.delivery_date,
                    OrderData.book_id,
                    OrderData.quantity,
                    UserAddress.city,
                    UserAddress.street,
                    UserAddress.house,
                    UserAddress.apartment,
                    UserAddress.comment,
                )
                .join(UserAddress, OrderData.address_id == UserAddress.address_id)
                .where(
                    and_(
                        OrderData.order_id == order_id,
                        OrderData.telegram_id == telegram_id,
                    )
                )
            )
            order_result = await session.execute(order_stmt)
            order_data = order_result.mappings().first()
            if not order_data:
                return None
            address_parts = []
            if order_data["city"]:
                address_parts.append(f"г.{order_data['city']}")
            if order_data["street"]:
                address_parts.append(f"ул.{order_data['street']}")
            if order_data["house"]:
                address_parts.append(f"д.{order_data['house']}")
            if order_data["apartment"]:
                address_parts.append(f"кв.{order_data['apartment']}")
            address = ", ".join(address_parts) if address_parts else "Не указан"
            items_text = ""
            items_list = []
            for i, book_id in enumerate(order_data["book_id"]):
                quantity = order_data["quantity"][i]
                book_stmt = select(Book.book_title, Book.book_price).where(
                    Book.book_id == book_id
                )
                book_result = await session.execute(book_stmt)
                book = book_result.mappings().first()
                if book:
                    item_price = book["book_price"] * quantity
                    items_text += f"• {book['book_title']} - {quantity}шт. × {book['book_price']}₽ = {item_price}₽\n"
                    items_list.append(
                        {
                            "book_title": book["book_title"],
                            "quantity": quantity,
                            "price": book["book_price"],
                            "total_price": item_price,
                        }
                    )
            return {
                "order_id": order_data["order_id"],
                "status": order_data["status"],
                "total_price": order_data["price"],
                "created_date": order_data["created_date"],
                "delivery_date": order_data["delivery_date"],
                "address": address,
                "comment": order_data["comment"],
                "items": items_text,
                "items_list": items_list,
                "telegram_id": telegram_id,
            }

    @staticmethod
    async def get_user_money_back(user_telegram_id: int, amount_money: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.user_balance).where(User.telegram_id == user_telegram_id)
            )
            current_balance = result.scalar_one_or_none()
            if current_balance is not None:
                await session.execute(
                    update(User)
                    .where(User.telegram_id == user_telegram_id)
                    .values(user_balance=User.user_balance + amount_money)
                )
            await session.commit()

    @staticmethod
    async def get_user_telegram_id_by_order_id(order_id: int) -> Optional[int]:
        async with AsyncSessionLocal() as session:
            query = select(OrderData.telegram_id).where(OrderData.order_id == order_id)
            result = await session.execute(query)
            telegram_id = result.scalar_one_or_none()
            return telegram_id

    @staticmethod
    async def get_order_with_user(order_id: int):
        async with AsyncSessionLocal() as session:
            query = (
                select(OrderData)
                .where(OrderData.order_id == order_id)
                .options(selectinload(OrderData.user))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_order_with_user_data(order_id: int):
        async with AsyncSessionLocal() as session:
            query = (
                select(OrderData)
                .where(OrderData.order_id == order_id)
                .options(selectinload(OrderData.user))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def check_cart_quantity_limit(
        telegram_id: int, book_id: int, quantity_to_add: int = 1
    ) -> dict:
        async with AsyncSessionLocal() as session:
            cart_query = (
                select(func.sum(CartItem.quantity))
                .join(Cart, Cart.cart_id == CartItem.cart_id)
                .where(Cart.telegram_id == telegram_id, CartItem.book_id == book_id)
            )
            current_in_cart = await session.scalar(cart_query)
            current_in_cart = current_in_cart or 0
            book_query = select(Book.book_quantity).where(Book.book_id == book_id)
            available_quantity = await session.scalar(book_query)
            available_quantity = available_quantity or 0
            total_after_add = current_in_cart + quantity_to_add
            return {
                "can_add": total_after_add <= available_quantity,
                "current_in_cart": current_in_cart,
                "available_quantity": available_quantity,
                "max_can_add": max(0, available_quantity - current_in_cart),
                "message": f"Доступно для добавления: {max(0, available_quantity - current_in_cart)} шт.",
            }


class AdminQueries:
    @staticmethod
    async def set_admin_new_name(admin_id: int, admin_name: str) -> bool:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Admin).where(Admin.admin_id == admin_id).values(name=admin_name)
            )
            await session.commit()
            return True

    @staticmethod
    async def delete_book(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Book).where(Book.book_id == book_id)
                )
                book = result.scalar_one_or_none()
                if book:
                    await session.delete(book)
                    await session.commit()
                    return True
                return False
            except Exception as e:
                await session.rollback()
                return False

    @staticmethod
    async def made_new_admin_get_id(telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            admin = Admin(
                telegram_id=telegram_id,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            return admin.admin_id

    @staticmethod
    async def is_user_in_db(username: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_admins_with_permission(required_permission: AdminPermission) -> list:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin.telegram_id).where(
                    Admin.permissions.op("&")(required_permission.value)
                    == required_permission.value
                )
            )
            admins = result.scalars().all()
            return admins

    @staticmethod
    async def admin_visited(appeal_id: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .values(admin_visit=True)
            )
            await session.commit()

    @staticmethod
    async def get_admin_by_telegram_id(telegram_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin).where(Admin.telegram_id == telegram_id)
            )
            admin = result.scalar_one_or_none()
            return admin

    @staticmethod
    async def get_username_by_telegram_id(telegram_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.username).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_admin_by_id(admin_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin).where(Admin.admin_id == admin_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def has_closed_appeals(admin_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            exists_query = (
                select(1)
                .where(
                    SupportAppeal.assigned_admin_id == admin_id,
                    SupportAppeal.status.in_(
                        [AppealStatus.CLOSED_BY_ADMIN, AppealStatus.CLOSED_BY_USER]
                    ),
                )
                .exists()
            )
            result = await session.execute(select(exists_query))
            return result.scalar()

    @staticmethod
    async def get_order_status(order_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(OrderData.status).where(OrderData.order_id == order_id)
            )
            return result.scalar()

    @staticmethod
    async def canceling_order_with_reason(order_id: int, admin_id: int, reason) -> bool:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(OrderData)
                .where(OrderData.order_id == order_id)
                .values(
                    status=OrderStatus.CANCELLED,
                    admin_id_who_canceled=admin_id,
                    reason_to_cancellation=reason,
                )
            )
            await session.commit()
            return True

    @staticmethod
    async def count_appeals_in_work(admin_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(SupportAppeal.appeal_id)).where(
                    and_(
                        SupportAppeal.status == AppealStatus.IN_WORK,
                        SupportAppeal.assigned_admin_id == admin_id,
                    )
                )
            )
            return result.scalar()

    @staticmethod
    async def get_closed_appeals(
        admin_id: int, page: int = 0, items_per_page: int = 10
    ) -> tuple[list, int]:
        async with AsyncSessionLocal() as session:
            total_count = await session.execute(
                select(func.count(SupportAppeal.appeal_id)).where(
                    SupportAppeal.assigned_admin_id == admin_id,
                    SupportAppeal.status.in_(
                        [AppealStatus.CLOSED_BY_ADMIN, AppealStatus.CLOSED_BY_USER]
                    ),
                )
            )
            total_count = total_count.scalar()
            result = await session.execute(
                select(
                    SupportAppeal.appeal_id,
                    SupportAppeal.updated_at,
                    SupportAppeal.status,
                    User.username,
                )
                .where(
                    SupportAppeal.assigned_admin_id == admin_id,
                    SupportAppeal.status.in_(
                        [AppealStatus.CLOSED_BY_ADMIN, AppealStatus.CLOSED_BY_USER]
                    ),
                )
                .join(User, User.telegram_id == SupportAppeal.telegram_id)
                .order_by(SupportAppeal.updated_at.desc())
                .offset(page * items_per_page)
                .limit(items_per_page)
            )
            return result.mappings().all(), total_count

    @staticmethod
    async def is_user_admin(telegram_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin).where(Admin.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_admin_name(telegram_id: int) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin).where(Admin.telegram_id == telegram_id)
            )
            admin = result.scalar_one_or_none()
            return admin.name if admin else "Администратор"

    # @staticmethod
    # async def admin_appeal_in_work_count(admin_id: int):
    #     async with AsyncSessionLocal() as session:
    #         result = await session.execute(
    #             select(func.count()).where(
    #                 and_(
    #                     SupportAppeal.assigned_admin_id == admin_id,
    #                     SupportAppeal.status == AppealStatus.IN_WORK,
    #                 )
    #             )
    #         )
    #         all_appeals_in_work = result.scalar()
    #         return all_appeals_in_work

    @staticmethod
    async def appeal_in_work_for_kb(admin_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    SupportAppeal.appeal_id, SupportAppeal.admin_visit, User.username
                )
                .where(
                    and_(
                        SupportAppeal.assigned_admin_id == admin_id,
                        SupportAppeal.status == AppealStatus.IN_WORK,
                    )
                )
                .join(User, User.telegram_id == SupportAppeal.telegram_id)
                .order_by(SupportAppeal.admin_visit)
            )
            appeals_data = result.mappings().all()
            return appeals_data

    @staticmethod
    async def get_new_appeal():
        async with AsyncSessionLocal() as session:
            appeal = await session.execute(
                select(SupportAppeal)
                .options(
                    selectinload(SupportAppeal.user_messages),
                    selectinload(SupportAppeal.admin_messages),
                    selectinload(SupportAppeal.user),
                )
                .where(
                    and_(
                        SupportAppeal.assigned_admin_id.is_(None),
                        SupportAppeal.status == AppealStatus.NEW,
                    )
                )
                .order_by(SupportAppeal.priority.desc(), SupportAppeal.created_date)
                .limit(1)
            )
            new_appeal = appeal.scalar_one_or_none()
            return new_appeal

    @staticmethod
    async def get_admin_appeal_by_id(appeal_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal)
                .options(
                    selectinload(SupportAppeal.user_messages),
                    selectinload(SupportAppeal.admin_messages).selectinload(
                        AdminMessage.admin
                    ),
                    selectinload(SupportAppeal.user),
                )
                .where(SupportAppeal.appeal_id == appeal_id)
            )
            appeal_data = result.scalar_one_or_none()
            return appeal_data

    @staticmethod
    async def assign_appeal_to_admin(appeal_id: int, admin_telegram_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            admin_query = select(Admin.admin_id).where(
                Admin.telegram_id == admin_telegram_id
            )
            admin_result = await session.execute(admin_query)
            admin_row = admin_result.first()
            if not admin_row:
                return False
            admin_id = admin_row[0]
            stmt = (
                update(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .values(
                    assigned_admin_id=admin_id,
                    status=AppealStatus.IN_WORK,
                    updated_at=datetime.now(),
                )
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def admin_support_to_user(
        admin_id: int, appeal_id: int, message: str
    ) -> bool:
        async with AsyncSessionLocal() as session:
            admin_msg = AdminMessage(
                admin_message=message, admin_id=admin_id, appeal_id=appeal_id
            )
            session.add(admin_msg)
            await session.execute(
                update(SupportAppeal)
                .where(SupportAppeal.appeal_id == appeal_id)
                .values(
                    status=AppealStatus.IN_WORK,
                    admin_visit=True,
                    updated_at=datetime.now(),
                )
            )
            await session.commit()
            return True

    @staticmethod
    async def appeal_exists(appeal_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SupportAppeal.appeal_id).where(
                    SupportAppeal.appeal_id == appeal_id
                )
            )
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_assigned_admin(appeal_id: int, admin_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            appeal = await session.execute(
                select(SupportAppeal.appeal_id)
                .where(
                    and_(
                        SupportAppeal.appeal_id == appeal_id,
                        SupportAppeal.assigned_admin_id == admin_id,
                    )
                )
                .limit(1)
            )
            is_assigned = appeal.scalar_one_or_none()
            return is_assigned is not None

    @staticmethod
    async def get_appeals_by_username(
        username: str,
        admin_id: int,
        has_admin_permission: bool,
        page: int = 0,
        items_per_page: int = 10,
    ) -> tuple[list, int]:
        async with AsyncSessionLocal() as session:
            query = (
                select(SupportAppeal)
                .join(SupportAppeal.user)
                .where(User.username == username)
            )
            if not has_admin_permission:
                query = query.where(SupportAppeal.assigned_admin_id == admin_id)
            total_count = await session.execute(
                select(func.count()).select_from(query.subquery())
            )
            total_count = total_count.scalar()
            result = await session.execute(
                query.options(joinedload(SupportAppeal.user))
                .order_by(SupportAppeal.updated_at.desc())
                .offset(page * items_per_page)
                .limit(items_per_page)
            )
            appeals = result.scalars().all()
            appeals_data = []
            for appeal in appeals:
                appeals_data.append(
                    {
                        "appeal_id": appeal.appeal_id,
                        "created_date": appeal.created_date,
                        "updated_at": appeal.updated_at,
                        "status": appeal.status,
                        "username": appeal.user.username
                        if appeal.user
                        else "Без username",
                    }
                )
            return appeals_data, total_count

    @staticmethod
    async def has_appeals_by_username(
        username: str, admin_id: int, has_admin_permission: bool
    ) -> bool:
        async with AsyncSessionLocal() as session:
            query = (
                select(SupportAppeal.appeal_id)
                .join(SupportAppeal.user)
                .where(User.username == username)
            )
            if not has_admin_permission:
                query = query.where(SupportAppeal.assigned_admin_id == admin_id)
            query = query.limit(1)
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_admins_info() -> dict:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin.permissions, func.count(Admin.admin_id)).group_by(
                    Admin.permissions
                )
            )
            stats = result.all()
            stats_dict = {}
            for permission, count in stats:
                if permission == AdminPermission.SUPER_ADMIN_PERMS:
                    stats_dict["super_admins"] = count
                elif permission == AdminPermission.ADMIN_PERMS:
                    stats_dict["admins"] = count
                elif permission == AdminPermission.MANAGER_PERMS:
                    stats_dict["managers"] = count
                elif permission == AdminPermission.MODERATOR_PERMS:
                    stats_dict["moderators"] = count
            stats_dict["total"] = sum(stats_dict.values())
            return stats_dict

    @staticmethod
    async def get_total_count_admins_by_lvl(admin_lvl) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(Admin.admin_id)).where(
                    Admin.role_name
                    == admin_role_dict.get(
                        admin_lvl
                    )  # dict on top of the all orm queries
                )
            )
            return result.scalar() or 0

    @staticmethod
    async def get_admin_role_by_admin_id(admin_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin.role_name).where(Admin.admin_id == admin_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def delete_admin(admin_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(Admin)
                .where(Admin.admin_id == admin_id)
                .values(permissions=AdminPermission.NONE, role_name=AdminRole.DELETED)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def update_admin_permissions_and_role(
        admin_id: int, permissions: int, role: str
    ):
        async with AsyncSessionLocal() as session:
            admin = await session.execute(
                select(Admin).where(Admin.admin_id == admin_id)
            )
            admin = admin.scalar_one_or_none()
            if not admin:
                return False
            admin.permissions = permissions
            admin.role_name = role
            admin.updated_at = datetime.utcnow()
            await session.commit()
            return True

    @staticmethod
    async def get_admins_paginated(
        admin_lvl: str, page: int = 0, items_per_page: int = 10
    ) -> list:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Admin.admin_id,
                    Admin.name,
                )
                .where(Admin.role_name == admin_role_dict.get(admin_lvl))
                .order_by(Admin.created_at.desc())
                .offset(page * items_per_page)
                .limit(items_per_page)
            )
            return result.mappings().all()

    @staticmethod
    async def get_admin_orders_count(order_type: str) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(OrderData.order_id)).where(
                    OrderData.status
                    == order_type_to_admin_orders_dict.get(
                        order_type
                    )  # dict on top of the all orm
                )
            )
            return result.scalar() or 0

    @staticmethod
    async def get_telegram_id_by_username(username: str) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.telegram_id).where(User.username == username)
            )
            return result.scalar() or 0

    @staticmethod
    async def get_admin_orders_count_telegram_id(telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(OrderData.order_id)).where(
                    OrderData.telegram_id == telegram_id
                )
            )
            return result.scalar() or 0

    @staticmethod
    async def admin_get_user_orders_by_telegram_id_small(
        telegram_id: int, page: int = 0, items_per_page: int = 10
    ) -> list:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    OrderData.order_id,
                    OrderData.price,
                    OrderData.created_date,
                    OrderData.book_id,
                    User.username,
                    User.user_first_name,
                )
                .where(OrderData.telegram_id == telegram_id)
                .join(User, User.telegram_id == OrderData.telegram_id)
                .order_by(OrderData.created_date.desc())
                .offset(page * items_per_page)
                .limit(items_per_page)
            )
            return result.mappings().all()

    @staticmethod
    async def get_admin_orders_paginated(
        order_type: str, page: int = 0, items_per_page: int = 10
    ) -> list:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    OrderData.order_id,
                    OrderData.price,
                    OrderData.created_date,
                    OrderData.book_id,
                    User.username,
                    User.user_first_name,
                )
                .where(
                    OrderData.status == order_type_to_admin_orders_dict.get(order_type)
                )
                .join(User, User.telegram_id == OrderData.telegram_id)
                .order_by(OrderData.created_date.desc())
                .offset(page * items_per_page)
                .limit(items_per_page)
            )
            return result.mappings().all()

    @staticmethod
    async def get_order_details(order_id: int) -> Optional[dict]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    OrderData.order_id,
                    OrderData.price,
                    OrderData.created_date,
                    OrderData.book_id,
                    OrderData.quantity,
                    OrderData.status,
                    OrderData.reason_to_cancellation,
                    OrderData.admin_id_who_canceled,
                    Admin.name.label("admin_name"),
                    Admin.admin_id,
                    User.username,
                    User.user_first_name,
                    User.telegram_id,
                    UserAddress.name.label("address_name"),
                    UserAddress.phone,
                    UserAddress.city,
                    UserAddress.street,
                    UserAddress.house,
                    UserAddress.apartment,
                    UserAddress.comment,
                )
                .where(OrderData.order_id == order_id)
                .join(User, User.telegram_id == OrderData.telegram_id)
                .join(UserAddress, UserAddress.address_id == OrderData.address_id)
                .outerjoin(Admin, OrderData.admin_id_who_canceled == Admin.admin_id)
            )
            order = result.mappings().first()
            if not order:
                return None
            books_info = []
            if order.book_id and order.quantity:
                for i, book_id in enumerate(order.book_id):
                    book_result = await session.execute(
                        select(Book.book_title, Book.book_price).where(
                            Book.book_id == book_id
                        )
                    )
                    book = book_result.mappings().first()
                    if book:
                        quantity = order.quantity[i] if i < len(order.quantity) else 1
                        books_info.append(
                            {
                                "book_id": book_id,
                                "title": book.book_title,
                                "price": book.book_price,
                                "quantity": quantity,
                            }
                        )
            return {
                "order_id": order.order_id,
                "total_price": order.price,
                "created_date": order.created_date,
                "status": order.status,
                "reason_to_cancellation": order.reason_to_cancellation,
                "admin_id_who_canceled": order.admin_id_who_canceled,
                "admin_name": order.admin_name,
                "admin_id": order.admin_id,
                "user": {
                    "username": order.username,
                    "first_name": order.user_first_name,
                    "telegram_id": order.telegram_id,
                },
                "address": {
                    "name": order.address_name,
                    "phone": order.phone,
                    "city": order.city,
                    "street": order.street,
                    "house": order.house,
                    "apartment": order.apartment,
                    "comment": order.comment,
                },
                "books": books_info,
            }

    @staticmethod
    async def get_order_new_status(order_id: int, new_status) -> dict:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(OrderData)
                .where(OrderData.order_id == order_id)
                .values(status=new_status)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def get_admin_by_username(username: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Admin)
                .join(User, Admin.telegram_id == User.telegram_id)
                .where(User.username == username)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def check_if_author_exist(author_name: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Author.author_id, Author.author_name, Author.author_country
                ).where(Author.author_name.ilike(f"%{author_name}%"))
            )
            return result.mappings().all()

    @staticmethod
    async def add_value_to_new_book(book_id: int, column: str, value) -> dict:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Book).where(Book.book_id == book_id).values({column: value})
            )
            await session.flush()
            await session.commit()

    @staticmethod
    async def assign_new_author_to_book(book_id: int, author_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(Book).where(Book.book_id == book_id).values(author_id=author_id)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def get_next_step_in_book_changes(book_id: int):
        async with AsyncSessionLocal() as session:
            query = select(
                case(
                    (Book.book_title.is_(None), "title"),
                    (Book.book_year.is_(None), "year"),
                    (Book.author_id.is_(None), "author"),
                    (Book.book_genre.is_(None), "genre"),
                    (Book.book_price.is_(None), "price"),
                    (Book.book_quantity.is_(None), "quantity"),
                    (Book.book_photo_id.is_(None), "cover"),
                    else_="complete",
                ).label("last_step")
            ).where(Book.book_id == book_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()


class StatisticsQueries:
    @staticmethod
    async def get_admin_support_statistics(telegram_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            admin_query = select(Admin.admin_id, Admin.name).where(
                Admin.telegram_id == telegram_id
            )
            admin_result = await session.execute(admin_query)
            admin_row = admin_result.first()
            if not admin_row:
                return {"error": "Администратор не найден"}
            admin_id, admin_name = admin_row
            sql_query = text("""
                SELECT 
                    -- ОБЩАЯ статистика системы
                    COUNT(sa.appeal_id) as total_appeals,
                    COUNT(CASE WHEN sa.created_date >= :today_start THEN 1 END) as appeals_today,
                    
                    -- Общая статистика по статусам за сегодня
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'new' THEN 1 END) as new_today,
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'in_work' THEN 1 END) as in_work_today,
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'closed_by_admin' THEN 1 END) as closed_by_admin_today,
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'closed_by_user' THEN 1 END) as closed_by_user_today,
                    
                    -- Статистика по приоритетам (только новые и в работе)
                    COUNT(CASE WHEN sa.priority = 'critical' AND sa.status IN ('new', 'in_work') THEN 1 END) as critical_count,
                    COUNT(CASE WHEN sa.priority = 'high' AND sa.status IN ('new', 'in_work') THEN 1 END) as high_count,
                    COUNT(CASE WHEN sa.priority = 'normal' AND sa.status IN ('new', 'in_work') THEN 1 END) as normal_count,
                    
                    -- ПЕРСОНАЛЬНАЯ статистика админа (обращения, которые он взял)
                    COUNT(CASE WHEN sa.assigned_admin_id = :admin_id AND sa.status = 'in_work' THEN 1 END) as admin_active,
                    COUNT(CASE WHEN sa.assigned_admin_id = :admin_id AND sa.status = 'closed_by_admin' THEN 1 END) as admin_closed,
                    
                    -- Статистика ответов админа (количество сообщений, которые он отправил сегодня)
                    (SELECT COUNT(am.message_id) 
                    FROM admin_messages am 
                    WHERE am.admin_id = :admin_id 
                    AND am.created_date >= :today_start) as admin_responses_today,
                    
                    -- Обращения, которые админ взял, но не ответил более 24 часов
                    COUNT(CASE WHEN 
                        sa.assigned_admin_id = :admin_id 
                        AND sa.status = 'in_work' 
                        AND sa.updated_at < NOW() - INTERVAL '24 hours'
                        THEN 1 END) as admin_overdue
                    
                FROM support_appeals sa
            """)
            params = {"today_start": today_start, "admin_id": admin_id}
            result = await session.execute(sql_query, params)
            row = result.fetchone()
            today_closed_total = (row.closed_by_admin_today or 0) + (
                row.closed_by_user_today or 0
            )
            return {
                # Общая статистика системы
                "total_appeals": row.total_appeals or 0,
                "appeals_today": row.appeals_today or 0,
                "new_appeals_today": row.new_today or 0,
                "in_work_today": row.in_work_today or 0,
                "closed_today_total": today_closed_total,
                "closed_by_admin_today": row.closed_by_admin_today or 0,
                "closed_by_user_today": row.closed_by_user_today or 0,
                # Статистика по приоритетам
                "critical_appeals": row.critical_count or 0,
                "high_priority_appeals": row.high_count or 0,
                "normal_priority_appeals": row.normal_count or 0,
                # ПЕРСОНАЛЬНАЯ статистика админа
                "admin_name": admin_name,
                "admin_active_appeals": row.admin_active or 0,
                "admin_closed_appeals": row.admin_closed or 0,
                "admin_responses_today": row.admin_responses_today or 0,
                "admin_overdue_appeals": row.admin_overdue or 0,
                # Временные метки
                "stats_date": today.strftime("%d.%m.%Y"),
                "generated_at": datetime.now().strftime("%H:%M"),
            }

    @staticmethod
    async def get_comprehensive_stats() -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    WITH revenue_stats AS (
                        SELECT 
                            -- Реализованная выручка (доставленные заказы)
                            COALESCE(SUM(CASE WHEN status = 'Доставлен✅' AND DATE(created_date) = CURRENT_DATE THEN price ELSE 0 END), 0) as realized_revenue_today,
                            COALESCE(SUM(CASE WHEN status = 'Доставлен✅' AND created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN price ELSE 0 END), 0) as realized_revenue_month,
                            COALESCE(SUM(CASE WHEN status = 'Доставлен✅' THEN price ELSE 0 END), 0) as realized_revenue_total,
                            
                            -- Общий объем продаж (все заказы)
                            COALESCE(SUM(CASE WHEN DATE(created_date) = CURRENT_DATE THEN price ELSE 0 END), 0) as total_sales_today,
                            COALESCE(SUM(CASE WHEN created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN price ELSE 0 END), 0) as total_sales_month,
                            COALESCE(SUM(price), 0) as total_sales_total,
                            
                            -- Ожидаемая выручка (заказы в процессе)
                            COALESCE(SUM(CASE WHEN status IN ('🚚Доставляется', 'В обработке⌛') AND DATE(created_date) = CURRENT_DATE THEN price ELSE 0 END), 0) as expected_revenue_today,
                            COALESCE(SUM(CASE WHEN status IN ('🚚Доставляется', 'В обработке⌛') AND created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN price ELSE 0 END), 0) as expected_revenue_month,
                            COALESCE(SUM(CASE WHEN status IN ('🚚Доставляется', 'В обработке⌛') THEN price ELSE 0 END), 0) as expected_revenue_total
                        FROM order_data
                    ),
                    order_stats AS (
                        SELECT 
                            COUNT(CASE WHEN DATE(created_date) = CURRENT_DATE THEN 1 END) as orders_today,
                            COUNT(CASE WHEN created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as orders_month,
                            COUNT(*) as orders_total,
                            COUNT(CASE WHEN status = '🚚Доставляется' THEN 1 END) as delivering_orders,
                            COUNT(CASE WHEN status = 'В обработке⌛' THEN 1 END) as processing_orders,
                            COUNT(CASE WHEN status = 'Доставлен✅' THEN 1 END) as completed_orders,
                            COUNT(CASE WHEN status = 'Отменен❌' AND DATE(created_date) = CURRENT_DATE THEN 1 END) as cancelled_today,
                            COUNT(CASE WHEN status = 'Отменен❌' AND created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as cancelled_month,
                            COUNT(CASE WHEN status = 'Отменен❌' THEN 1 END) as cancelled_total
                        FROM order_data
                    ),
                    user_stats AS (
                        SELECT COUNT(*) as total_users FROM users
                    ),
                    admin_stats AS (
                        SELECT COUNT(*) as total_admins FROM admins
                    ),
                    genre_stats AS (
                        SELECT 
                            json_object_agg(book_genre, genre_count) as genres
                        FROM (
                            SELECT book_genre, COUNT(*) as genre_count
                            FROM books 
                            WHERE book_genre IS NOT NULL 
                            GROUP BY book_genre
                        ) genre_counts
                    ),
                    book_stats AS (
                        SELECT 
                            COUNT(*) as total_books,
                            COUNT(CASE WHEN book_status = 'out of stock' THEN 1 END) as out_of_stock_books
                        FROM books
                    ),
                    appeal_stats AS (
                        SELECT 
                            COUNT(*) as active_appeals,
                            COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_appeals
                        FROM support_appeals 
                        WHERE status IN ('new', 'in_work')
                    ),
                    role_stats AS (
                        SELECT 
                            json_object_agg(role_name, role_count) as roles
                        FROM (
                            SELECT role_name, COUNT(*) as role_count
                            FROM admins 
                            GROUP BY role_name
                        ) role_counts
                    )
                    
                    SELECT 
                        rev.realized_revenue_today, rev.realized_revenue_month, rev.realized_revenue_total,
                        rev.total_sales_today, rev.total_sales_month, rev.total_sales_total,
                        rev.expected_revenue_today, rev.expected_revenue_month, rev.expected_revenue_total,
                        os.orders_today, os.orders_month, os.orders_total, 
                        os.delivering_orders, os.processing_orders, os.completed_orders,
                        os.cancelled_today, os.cancelled_month, os.cancelled_total,
                        us.total_users,
                        ads.total_admins,
                        bs.total_books,
                        bs.out_of_stock_books,
                        gs.genres as books_by_genre,
                        aps.active_appeals,
                        aps.critical_appeals,
                        rls.roles as admins_by_role
                    FROM revenue_stats rev,
                        order_stats os, 
                        user_stats us, 
                        admin_stats ads, 
                        book_stats bs, 
                        genre_stats gs,
                        appeal_stats aps,
                        role_stats rls
                """)
                result = await session.execute(query)
                row = result.mappings().first()
                if not row:
                    return {"error": "No data found"}
                return {
                    # Выручка
                    "realized_revenue_today": row["realized_revenue_today"] or 0,
                    "realized_revenue_month": row["realized_revenue_month"] or 0,
                    "realized_revenue_total": row["realized_revenue_total"] or 0,
                    "total_sales_today": row["total_sales_today"] or 0,
                    "total_sales_month": row["total_sales_month"] or 0,
                    "total_sales_total": row["total_sales_total"] or 0,
                    "expected_revenue_today": row["expected_revenue_today"] or 0,
                    "expected_revenue_month": row["expected_revenue_month"] or 0,
                    "expected_revenue_total": row["expected_revenue_total"] or 0,
                    # Заказы
                    "orders_today": row["orders_today"] or 0,
                    "orders_month": row["orders_month"] or 0,
                    "orders_total": row["orders_total"] or 0,
                    "delivering_orders": row["delivering_orders"] or 0,
                    "processing_orders": row["processing_orders"] or 0,
                    "completed_orders": row["completed_orders"] or 0,
                    "cancelled_today": row["cancelled_today"] or 0,
                    "cancelled_month": row["cancelled_month"] or 0,
                    "cancelled_total": row["cancelled_total"] or 0,
                    # Остальное
                    "total_users": row["total_users"] or 0,
                    "total_admins": row["total_admins"] or 0,
                    "total_books": row["total_books"] or 0,
                    "out_of_stock_books": row["out_of_stock_books"] or 0,
                    "books_by_genre": row["books_by_genre"] or {},
                    "active_appeals": row["active_appeals"] or 0,
                    "critical_appeals": row["critical_appeals"] or 0,
                    "admins_by_role": row["admins_by_role"] or {},
                }
            except Exception as e:
                print(f"Error getting statistics: {e}")
                return {"error": str(e)}

    @staticmethod
    async def _get_admins_by_role(session):
        """Дополнительный запрос для получения админов по ролям"""
        query = text(
            "SELECT role_name, COUNT(*) as count FROM admins GROUP BY role_name"
        )
        result = await session.execute(query)
        return {row.role_name: row.count for row in result.all()}

    @staticmethod
    async def orders_statistic() -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    WITH order_stats AS (
                        SELECT 
                            COUNT(CASE WHEN DATE(created_date) = CURRENT_DATE THEN 1 END) as orders_today,
                            COUNT(CASE WHEN created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as orders_month,
                            COUNT(*) as orders_total,
                            COUNT(CASE WHEN status = '🚚Доставляется' THEN 1 END) as delivering_orders,
                            COUNT(CASE WHEN status = 'В обработке⌛' THEN 1 END) as processing_orders,
                            COUNT(CASE WHEN status = 'Доставлен✅' THEN 1 END) as completed_orders,
                            COUNT(CASE WHEN status = 'Отменен❌' AND DATE(created_date) = CURRENT_DATE THEN 1 END) as cancelled_today,
                            COUNT(CASE WHEN status = 'Отменен❌' AND created_date >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as cancelled_month,
                            COUNT(CASE WHEN status = 'Отменен❌' THEN 1 END) as cancelled_total
                        FROM order_data
                    )
                    SELECT * FROM order_stats
                """)

                result = await session.execute(query)
                row = result.mappings().first()

                if not row:
                    return {"error": "No data found"}

                return {
                    "orders_today": row["orders_today"] or 0,
                    "orders_month": row["orders_month"] or 0,
                    "orders_total": row["orders_total"] or 0,
                    "delivering_orders": row["delivering_orders"] or 0,
                    "processing_orders": row["processing_orders"] or 0,
                    "completed_orders": row["completed_orders"] or 0,
                    "cancelled_today": row["cancelled_today"] or 0,
                    "cancelled_month": row["cancelled_month"] or 0,
                    "cancelled_total": row["cancelled_total"] or 0,
                }

            except Exception as e:
                print(f"Error getting orders statistics: {e}")
                return {"error": str(e)}


class DBData:
    @staticmethod
    async def add_other_data():
        async with AsyncSessionLocal() as session:
            book = Book(
                book_title="La Divina Commedi",
                book_year=1321,
                author_id=1,
                book_price=1990,
                book_status=BookStatus.IN_STOCK,
                book_genre=BookGenre.CLASSIC,
                book_quantity=3,
            )
            second_book = Book(
                book_title="La Vita Nuova",
                book_year=1295,
                author_id=1,
                book_price=1490,
                book_status=BookStatus.IN_STOCK,
                book_genre=BookGenre.CLASSIC,
                book_quantity=2,
            )
            user = User(
                username="sentrybuster",
                user_first_name="Artem",
                telegram_id=717149416,
            )
            cart = Cart(telegram_id=717149416)
            review = Review(
                book_id=2,
                review_rating=5,
                review_title="Best book ever",
                review_body="The best book I've ever read",
                telegram_id=123123123,
                finished=True,
                published=True,
            )
            second_review = Review(
                book_id=2,
                review_rating=3,
                review_title="I think it's alright",
                review_body="I mean maybe not the best book that I've known but it still kind nice",
                telegram_id=1241413412,
                finished=True,
                published=True,
            )
            session.add_all([book, cart, second_book, user, review, second_review])
            await session.commit()

    @staticmethod
    async def fake_data():
        async with AsyncSessionLocal() as session:
            # Создаем основного пользователя и админа
            user = User(
                username="@sentrybuster",
                user_first_name="Artem",
                telegram_id=717149416,
            )
            cart = Cart(telegram_id=user.telegram_id)
            user.cart = cart
            session.add_all([user, cart])

            admin = Admin(
                telegram_id=717149416,
                name="Артём",
                permissions=AdminPermission.SUPER_ADMIN_PERMS,
                role_name="super_admin",
            )
            session.add(admin)
            await session.flush()
            await session.commit()

            # # Создаем авторов
            # authors = [
            #     Author(author_name=fake.name(), author_country=fake.country())
            #     for _ in range(25)
            # ]
            # session.add(admin)
            # session.add_all(authors)
            # await session.flush()

            # # Создаем книги
            # books = [
            #     Book(
            #         book_title=fake.sentence(nb_words=3)[:-1],
            #         book_year=random.randint(1990, 2023),
            #         author_id=random.choice(authors).author_id,
            #         book_status=random.choice(list(BookStatus)),
            #         book_price=random.randint(400, 3000),
            #         book_photo_id="AgACAgIAAxkBAAISfGkV5uHsE7KI41KLjrCTaTHCeedPAALhDWsb25uwSCWYDAlTnDwWAQADAgADeQADNgQ",
            #         book_in_stock=True,
            #         book_genre=random.choice(list(BookGenre)),
            #         book_quantity=random.randint(1, 9),
            #     )
            #     for _ in range(50)
            # ]
            # session.add_all(books)
            # await session.flush()

            for author_data in REAL_AUTHORS:
                author = Author(
                    author_name=author_data["author_name"],
                    author_country=author_data["author_country"],
                    author_add_date=author_data.get("author_add_date", datetime.now()),
                )
                session.add(author)
                await session.flush()
            await session.commit()

            for book_data in REAL_BOOKS:
                book = Book(
                    book_title=book_data["book_title"],
                    book_year=book_data["book_year"],
                    author_id=book_data["author_id"],
                    book_status=book_data["book_status"],
                    book_price=book_data["book_price"],
                    book_photo_id=book_data["book_photo_id"],
                    book_in_stock=book_data["book_in_stock"],
                    book_genre=book_data["book_genre"],
                    book_quantity=book_data["book_quantity"],
                )
                session.add(book)
                await session.flush()
            await session.commit()

            # Создаем дополнительных пользователей
            users = []
            for _ in range(25):
                user = User(
                    username=fake.user_name()[:30],
                    user_first_name=fake.name()[:30],
                    telegram_id=random.randint(38712, 129312239),
                )
                cart = Cart(telegram_id=user.telegram_id)
                user.cart = cart
                users.append(user)
                session.add(user)

            await session.flush()

            # # Создаем отзывы
            # book_ids = [book.book_id for book in books]
            # user_ids = [user.telegram_id for user in users]

            # reviews = [
            #     Review(
            #         book_id=random.choice(book_ids),
            #         telegram_id=random.choice(user_ids),
            #         review_rating=random.randint(1, 3),
            #         review_title=fake.sentence(nb_words=3)[:100],
            #         review_body=fake.paragraph(nb_sentences=3)[:900],
            #         created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
            #         finished=True,
            #         published=True,
            #     )
            #     for _ in range(70)
            # ]
            # session.add_all(reviews)

            # reviews2 = [
            #     Review(
            #         book_id=random.choice(book_ids),
            #         telegram_id=random.choice(user_ids),
            #         review_rating=random.randint(3, 5),
            #         review_title=fake.sentence(nb_words=3)[:100],
            #         review_body=fake.paragraph(nb_sentences=3)[:900],
            #         created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
            #         finished=True,
            #         published=True,
            #     )
            #     for _ in range(250)
            # ]
            # session.add_all(reviews2)

            # Создаем элемент корзины
            # cart_item = CartItem(
            #     cart_id=1,
            #     cart_items_id=1,
            #     book_id=15,
            #     quantity=1,
            #     price=1000,
            # )
            # session.add(cart_item)
            address = UserAddress(
                address_id=1,
                telegram_id=717149416,
                name="Артём",
                phone="89139999957",
                city="Москва",
                street="Бронный переулок",
                house="1",
                apartment="234",
                is_complete=True,
            )
            session.add(address)

            # # Получаем всех пользователей и админов
            # all_users_result = await session.execute(select(User))
            # all_users = all_users_result.scalars().all()

            # all_admins_result = await session.execute(select(Admin))
            # all_admins = all_admins_result.scalars().all()

            # if not all_users or not all_admins:
            #     print("❌ Нет пользователей или админов для создания обращений")
            #     return

            # support_appeals = []
            # user_messages = []
            # admin_messages = []

            # # Текущее время и даты для разных периодов
            # now = datetime.now()
            # today = now.date()
            # yesterday = today - timedelta(days=1)
            # last_week = today - timedelta(days=7)

            # priorities = ["low", "normal", "high", "critical"]

            # # Создаем 25 тестовых обращений с правильным распределением статусов
            # for i in range(25):
            #     user = random.choice(all_users)

            #     # Распределяем статусы:
            #     # - 40% новых обращений (без назначенного админа)
            #     # - 30% в работе (с назначенным админом)
            #     # - 15% закрыто пользователем
            #     # - 15% закрыто админом (с назначенным админом)
            #     if i < 10:  # 40% - Новые обращения
            #         status = AppealStatus.NEW
            #         admin = None  # Без назначенного админа
            #         created_date = now - timedelta(hours=random.randint(1, 23))
            #     elif i < 17:  # 28% - В работе
            #         status = AppealStatus.IN_WORK
            #         admin = random.choice(all_admins)  # С назначенным админом
            #         created_date = datetime.combine(yesterday, now.time()) - timedelta(
            #             hours=random.randint(1, 23)
            #         )
            #     elif i < 21:  # 16% - Закрыто пользователем
            #         status = AppealStatus.CLOSED_BY_USER
            #         admin = (
            #             random.choice(all_admins) if random.random() > 0.5 else None
            #         )  # 50% с админом
            #         created_date = datetime.combine(last_week, now.time()) + timedelta(
            #             days=random.randint(0, 6)
            #         )
            #     else:  # 16% - Закрыто админом
            #         status = AppealStatus.CLOSED_BY_ADMIN
            #         admin = random.choice(all_admins)  # Всегда с назначенным админом
            #         created_date = datetime.combine(last_week, now.time()) - timedelta(
            #             days=random.randint(8, 30)
            #         )

            #     priority = random.choice(priorities)

            # # Создаем обращение
            # appeal = SupportAppeal(
            #     telegram_id=user.telegram_id,
            #     created_date=created_date,
            #     updated_at=created_date,
            #     status=status,
            #     priority=priority,
            #     assigned_admin_id=admin.admin_id if admin else None,
            # )
            # support_appeals.append(appeal)
            # session.add(appeal)

            # await session.flush()  # Получаем ID для созданных обращений

            # Создаем сообщения для обращений
            # for appeal in support_appeals:
            #     # Сообщения от пользователя (1-3 сообщения)
            #     user_msg_count = random.randint(1, 3)
            #     for j in range(user_msg_count):
            #         user_message = UserMessage(
            #             telegram_id=appeal.telegram_id,
            #             message=f"Тестовое сообщение от пользователя #{j + 1}: {fake.paragraph(nb_sentences=2)}",
            #             created_date=appeal.created_date + timedelta(minutes=j * 10),
            #             appeal_id=appeal.appeal_id,
            #         )
            #         user_messages.append(user_message)
            #         session.add(user_message)

            # Сообщения от админа (только для обращений с назначенным админом и не новых)
            # if appeal.assigned_admin_id and appeal.status != AppealStatus.NEW:
            #     admin_msg_count = random.randint(1, 2)
            #     for k in range(admin_msg_count):
            #         admin_message = AdminMessage(
            #             admin_id=appeal.assigned_admin_id,
            #             admin_message=f"Тестовый ответ админа #{k + 1}: {fake.paragraph(nb_sentences=2)}",
            #             appeal_id=appeal.appeal_id,
            #             created_date=appeal.created_date + timedelta(hours=1 + k),
            #         )
            #         admin_messages.append(admin_message)
            #         session.add(admin_message)

            # # Обновляем updated_at для некоторых обращений
            # if random.random() > 0.7:
            #     appeal.updated_at = appeal.created_date + timedelta(
            #         hours=random.randint(1, 24)
            #     )

            # # Собираем статистику ДО коммита
            # new_count = len(
            #     [a for a in support_appeals if a.status == AppealStatus.NEW]
            # )
            # in_work_count = len(
            #     [a for a in support_appeals if a.status == AppealStatus.IN_WORK]
            # )
            # closed_by_user_count = len(
            #     [a for a in support_appeals if a.status == AppealStatus.CLOSED_BY_USER]
            # )
            # closed_by_admin_count = len(
            #     [a for a in support_appeals if a.status == AppealStatus.CLOSED_BY_ADMIN]
            # )

            # # Статистика по назначениям
            # assigned_count = len(
            #     [a for a in support_appeals if a.assigned_admin_id is not None]
            # )
            # unassigned_count = len(
            #     [a for a in support_appeals if a.assigned_admin_id is None]
            # )

            # # Получаем временные метки
            # created_dates = [a.created_date for a in support_appeals]
            # oldest_appeal = min(created_dates) if created_dates else now
            # newest_appeal = max(created_dates) if created_dates else now

            await session.commit()

            # Выводим статистику
            print("✅ Тестовые данные успешно сгенерированы ✅")

    #         print(f"""
    # 📊 СТАТИСТИКА СОЗДАННЫХ ДАННЫХ:

    # 📚 Основные данные:
    # • Пользователей: {len(all_users) + 1}  (+1 основной)
    # • Админов: {len(all_admins)}
    # • Книг: {len(books)}
    # • Авторов: {len(authors)}
    # • Отзывов: {len(reviews) + len(reviews2)}

    # 📞 Данные поддержки:
    # • Обращений: {len(support_appeals)}
    # ├─ Новые (NEW): {new_count} (без назначения)
    # ├─ В работе (IN_WORK): {in_work_count} (с назначением)
    # ├─ Закрыто пользователями: {closed_by_user_count}
    # └─ Закрыто админами: {closed_by_admin_count} (с назначением)

    # 📋 Назначения:
    # • С назначенным админом: {assigned_count}
    # • Без назначения: {unassigned_count}

    # 💬 Сообщений:
    # • От пользователей: {len(user_messages)}
    # • От админов: {len(admin_messages)}

    # 🕒 Временной диапазон обращений:
    # • Самое старое: {oldest_appeal.strftime("%d.%m.%Y %H:%M")}
    # • Самое новое: {newest_appeal.strftime("%d.%m.%Y %H:%M")}

    # 💡 Для тестирования:
    # • Новые обращения можно брать через "Взять новое обращение"
    # • Обращения в работе уже назначены на админов
    # • Закрытые обращения показывают историю работы
    #         """)

    @staticmethod
    async def clear_all_data():
        """Очистка ВСЕХ тестовых данных"""
        async with AsyncSessionLocal() as session:
            # Удаляем в правильном порядке (сначала дочерние таблицы)
            tables = [
                AdminMessage,
                UserMessage,
                SupportAppeal,
                CartItem,
                Review,
                Cart,
                User,
                Book,
                Author,
                Admin,
            ]

            for table in tables:
                await session.execute(table.__table__.delete())

            await session.commit()
            print("✅ Все тестовые данные очищены ✅")
