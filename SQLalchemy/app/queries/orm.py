from database import AsyncSessionLocal
from models import (
    Author,
    Book,
    User,
    Review,
    BookStatus,
    OrderStatus,
    BookGenre,
    Cart,
    CartItem,
    UserAddress,
    OrderData,
)
from faker import Faker
import random
from datetime import datetime, timedelta
from sqlalchemy import case, select, text, func, and_, update, or_


fake = Faker("ru_RU")


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
                .where(and_(Book.book_genre == genre, Review.finished))
                .join(Review, Book.book_id == Review.book_id)
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
                .join(Review, Review.book_id == Book.book_id)
                .join(Author, Book.author_id == Author.author_id, isouter=True)
                .where(and_(Book.book_id == book_id_int, Review.finished))
                .group_by(
                    Book.book_id,
                    Author.author_id,
                )
            )
            result = await session.execute(query)
            return result.mappings().first()

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
                .join(Author, Book.author_id == Author.author_id, isouter=True)
                .join(Review, Review.book_id == Book.book_id, isouter=True)
                .where(and_(Book.book_id == book_id_int, Review.finished))
                .group_by(Book.book_id, Book.book_title, Author.author_name)
            )
            book_result = await session.execute(book_query)
            book_info = book_result.mappings().first()
            reviews_query = (
                select(
                    Review.review_id,
                    Review.review_rating,
                    Review.review_title,
                    Review.review_body,
                )
                .join(User, Review.telegram_id == User.telegram_id, isouter=True)
                .where(and_(Review.book_id == book_id_int, Review.finished))
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
                    .values(book_quantity=Book.book_quantity - quantity_to_decrease)
                )
            await session.commit()

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

    @staticmethod
    async def get_sale_genre(genre):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Book.book_id,
                    Book.book_title,
                    Book.sale_value,
                    func.avg(Review.review_rating).label("book_rating"),
                )
                .where(
                    and_(Book.book_genre == genre, Book.book_on_sale, Review.finished)
                )
                .group_by(Book.book_id)
                .order_by(Book.sale_value.desc())
            )
            return result.mappings().all()
            # returning dict


class UserQueries:
    # @staticmethod
    # async def update_user(user_id: int, new_username: str):
    #     async with AsyncSessionLocal() as session:
    #         user = await session.get(User, user_id)
    #         user.username = new_username
    #         await session.commit()

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
            }


class SupportQueries:
    pass


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
            )
            second_review = Review(
                book_id=2,
                review_rating=3,
                review_title="I think it's alright",
                review_body="I mean maybe not the best book that I've known but it still kind nice",
                telegram_id=1241413412,
                finished=True,
            )
            session.add_all(
                [
                    book,
                    cart,
                    second_book,
                    user,
                    review,
                    second_review,
                ]
            )
            await session.commit()

    @staticmethod
    async def fake_data():
        async with AsyncSessionLocal() as session:
            user = User(
                username="Sentrybuster",
                user_first_name="Artem",
                telegram_id=717149416,
            )
            cart = Cart(telegram_id=user.telegram_id)
            user.cart = cart
            session.add_all([user, cart])
            authors = [
                Author(author_name=fake.name(), author_country=fake.country())
                for _ in range(25)
            ]
            session.add_all(authors)
            await session.flush()
            books = [
                Book(
                    book_title=fake.sentence(nb_words=3)[:-1],
                    book_year=random.randint(1990, 2023),
                    author_id=random.choice(authors).author_id,
                    book_status=random.choice(list(BookStatus)),
                    book_price=random.randint(400, 3000),
                    book_genre=random.choice(list(BookGenre)),
                    book_quantity=random.randint(1, 9),
                )
                for _ in range(50)
            ]
            session.add_all(books)
            await session.flush()
            for _ in range(25):
                users = []
                user = User(
                    username=fake.user_name()[:30],
                    user_first_name=fake.name()[:30],
                    telegram_id=random.randint(38712, 129312239),
                )
                cart = Cart(telegram_id=user.telegram_id)
                user.cart = cart
                users.append(user)
                session.add_all(users)
            await session.flush()
            book_ids = [book.book_id for book in books]
            user_ids = [user.telegram_id for user in users]
            reviews = [
                Review(
                    book_id=random.choice(book_ids),
                    telegram_id=random.choice(user_ids),
                    review_rating=random.randint(1, 3),
                    review_title=fake.sentence(nb_words=3)[:100],
                    review_body=fake.paragraph(nb_sentences=3)[:900],
                    created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                    finished=True,
                )
                for _ in range(70)
            ]
            session.add_all(reviews)
            await session.commit()
            reviews = [
                Review(
                    book_id=random.choice(book_ids),
                    telegram_id=random.choice(user_ids),
                    review_rating=random.randint(3, 5),
                    review_title=fake.sentence(nb_words=3)[:100],
                    review_body=fake.paragraph(nb_sentences=3)[:900],
                    created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                    finished=True,
                )
                for _ in range(250)
            ]
            cart_item = CartItem(
                cart_id=1,
                cart_items_id=1,
                book_id=15,
                quantity=1,
                price=1000,
            )
            session.add_all(reviews)
            session.add(cart_item)
            await session.commit()
        print("✅ Тестовые данные успешно сгенерированы ✅")
