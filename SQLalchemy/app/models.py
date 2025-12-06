from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    CheckConstraint,
    text,
    Numeric,
    BigInteger,
    Boolean,
    Float,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base
from typing import List, Annotated, Optional
from enum import Enum, IntFlag
from datetime import datetime


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


created_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("CAST(TIMEZONE('utc', now()) AS TIMESTAMP(0))"),
        nullable=False,
    ),
]
updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("CAST(TIMEZONE('utc', now()) AS TIMESTAMP(0))"),
        onupdate=text("CAST(TIMEZONE('utc', now()) AS TIMESTAMP(0))"),
        nullable=False,
    ),
]


class Payment(str, Enum):
    CARD = "card"
    BOT_WALLET = "bot_wallet"


class BookGenre(str, Enum):
    FANTASY = "fantasy"
    HORROR = "horror"
    SCIENCEFICTION = "sciencefiction"
    DETECTIVE = "detective"
    CLASSIC = "classic"
    POETRY = "poetry"


class OrderStatus(str, Enum):
    PROCESSING = "В обработке⌛"
    DELIVERING = "В доставке🚚"
    COMPLETED = "Доставлен✅"
    CANCELLED = "Отменен❌"


class PriorityStatus(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BookStatus(str, Enum):
    PENDING = "pending"
    IN_STOCK = "in stock"
    OUT_OF_STOCK = "out of stock"
    ARCHIVED = "archived"


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    MODERATOR = "moderator"
    DELETED = "deleted"
    NEW = "new"


class AppealStatus(str, Enum):
    NEW = "new"
    IN_WORK = "in_work"
    CLOSED_BY_USER = "closed_by_user"
    CLOSED_BY_ADMIN = "closed_by_admin"


class AdminPermission(IntFlag):
    NONE = 0
    MANAGE_SUPPORT = 1  # 00000001 - Управление поддержкой
    MANAGE_ORDERS = 2  # 00000010 - Управление заказами
    MANAGE_BOOKS = 4  # 00000100 - Управление книгами
    VIEW_STATS = 8  # 00001000 - Просмотр статистики
    MANAGE_ADMINS = 16  # 00010000 - Управление админами

    # Комбинации для ролей
    MODERATOR_PERMS = MANAGE_SUPPORT
    MANAGER_PERMS = MODERATOR_PERMS | MANAGE_ORDERS | MANAGE_BOOKS
    ADMIN_PERMS = MANAGER_PERMS | MANAGE_ADMINS
    SUPER_ADMIN_PERMS = (
        VIEW_STATS | MANAGE_ORDERS | MANAGE_BOOKS | MANAGE_SUPPORT | MANAGE_ADMINS
    )


class Author(Base):
    __tablename__ = "authors"
    author_id: Mapped[intpk]
    author_name: Mapped[str] = mapped_column(String(90), index=True)
    author_country: Mapped[str] = mapped_column(String(80), index=True, nullable=True)
    author_add_date: Mapped[created_at]
    author_books: Mapped[List["Book"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Book(Base):
    __tablename__ = "books"
    book_id: Mapped[intpk]
    book_title: Mapped[str] = mapped_column(
        index=True,
        nullable=True,
    )
    book_year: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=True,
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("authors.author_id"),
        index=True,
        nullable=True,
    )
    book_status: Mapped[BookStatus] = mapped_column(
        String(20),
        nullable=False,
        default=BookStatus.PENDING,
    )
    book_on_sale: Mapped[bool] = mapped_column(
        Boolean, index=True, nullable=True, server_default=text("FALSE")
    )
    sale_value: Mapped[float] = mapped_column(
        Float,
        CheckConstraint("sale_value >= 0 AND sale_value <= 1"),
        server_default="0",
    )  # 0.1 = 10%, 1 = 100%
    book_in_stock: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    book_photo_id: Mapped[str] = mapped_column(String, nullable=True)
    book_price: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("book_price >= 0"),
        nullable=True,
    )
    book_add_date: Mapped[created_at]
    book_genre: Mapped[BookGenre] = mapped_column(
        String(45),
        nullable=True,
    )
    book_quantity: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=True,
    )
    author: Mapped["Author"] = relationship(back_populates="author_books")
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="reviewed_book", cascade="all, delete-orphan"
    )


class Cart(Base):
    __tablename__ = "carts"
    cart_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    user: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    cart_items_id: Mapped[intpk]
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.cart_id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.book_id"), nullable=True)
    quantity: Mapped[int] = mapped_column(default=1, nullable=True)
    price: Mapped[int] = mapped_column(Integer, CheckConstraint("price >= 0"))
    cart: Mapped["Cart"] = relationship(back_populates="items")
    book: Mapped["Book"] = relationship()


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(30), index=True)
    user_first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    registration_date: Mapped[created_at]
    user_balance: Mapped[Numeric] = mapped_column(
        Numeric(10, 2),
        default=50000,
    )
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cart: Mapped["Cart"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
        uselist=False,
    )
    order_data: Mapped[List["OrderData"]] = relationship(back_populates="user")
    address: Mapped[List["UserAddress"]] = relationship(back_populates="user")
    appeals: Mapped[List["SupportAppeal"]] = relationship(back_populates="user")
    messages: Mapped[List["UserMessage"]] = relationship(back_populates="user")


class Admin(Base):
    __tablename__ = "admins"
    admin_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[Optional[str]]
    permissions: Mapped[int] = mapped_column(Integer, default=AdminPermission.NONE)
    role_name: Mapped[AdminRole] = mapped_column(String(20), default=AdminRole.NEW)
    # total_message_count: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    messages: Mapped[List["AdminMessage"]] = relationship(back_populates="admin")


class Review(Base):
    __tablename__ = "reviews"
    review_id: Mapped[intpk]
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.book_id"))
    review_rating: Mapped[int] = mapped_column(
        Integer, CheckConstraint("review_rating BETWEEN 0 AND 5"), index=True
    )
    review_title: Mapped[str] = mapped_column(String(100), nullable=True)
    review_body: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # review_photo_id: Mapped[List[int]] = mapped_column(nullable=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    finished: Mapped[bool] = mapped_column(Boolean, server_default="FALSE")
    published: Mapped[bool] = mapped_column(Boolean, server_default="FALSE")
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    reviewed_book: Mapped["Book"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship(back_populates="reviews")


class OrderData(Base):
    __tablename__ = "order_data"
    order_id: Mapped[intpk]
    address_id: Mapped[int] = mapped_column(ForeignKey("users_addresses.address_id"))
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    book_id: Mapped[list[int]] = mapped_column(JSON)
    quantity: Mapped[list[int]] = mapped_column(JSON)
    delivery_date: Mapped[str] = mapped_column(String, nullable=True)
    created_date: Mapped[created_at]
    updated_at: Mapped[updated_at]
    price: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(
        String(20), nullable=False, default=OrderStatus.PROCESSING
    )
    reason_to_cancellation: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    admin_id_who_canceled: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user: Mapped["User"] = relationship(back_populates="order_data")


class UserAddress(Base):
    __tablename__ = "users_addresses"
    address_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    name: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String(12), nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    street: Mapped[str] = mapped_column(String, nullable=True)
    house: Mapped[str] = mapped_column(String, nullable=True)
    apartment: Mapped[str] = mapped_column(String, nullable=True)
    payment: Mapped[Payment] = mapped_column(String, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    created_date: Mapped[created_at]
    updated_at: Mapped[updated_at]
    user: Mapped["User"] = relationship(back_populates="address")


class AdminMessage(Base):
    __tablename__ = "admin_messages"
    __table_args__ = (Index("ix_admin_messages_appeal_id", "appeal_id"),)
    message_id: Mapped[intpk]
    admin_message: Mapped[str] = mapped_column(String(500))
    admin_id: Mapped[int] = mapped_column(Integer, ForeignKey("admins.admin_id"))
    appeal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("support_appeals.appeal_id")
    )
    created_date: Mapped[created_at]
    appeal: Mapped["SupportAppeal"] = relationship(back_populates="admin_messages")
    admin: Mapped["Admin"] = relationship(back_populates="messages")


class UserMessage(Base):
    __tablename__ = "user_messages"
    message_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    message: Mapped[str] = mapped_column(String(1500))
    created_date: Mapped[created_at]
    appeal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("support_appeals.appeal_id")
    )
    appeal: Mapped["SupportAppeal"] = relationship(back_populates="user_messages")
    user: Mapped["User"] = relationship(back_populates="messages")


class SupportAppeal(Base):
    __tablename__ = "support_appeals"
    appeal_id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    user_messages: Mapped[List["UserMessage"]] = relationship(
        back_populates="appeal", cascade="all, delete-orphan"
    )
    admin_messages: Mapped[List["AdminMessage"]] = relationship(
        back_populates="appeal", cascade="all, delete-orphan"
    )
    created_date: Mapped[created_at]
    updated_at: Mapped[updated_at]
    status: Mapped[AppealStatus] = mapped_column(
        String(30), server_default=AppealStatus.NEW
    )
    user: Mapped["User"] = relationship(back_populates="appeals")
    assigned_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.admin_id"), nullable=True
    )
    priority: Mapped[str] = mapped_column(
        String(10), server_default=PriorityStatus.NORMAL
    )
    admin_initiative: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE")
    )
    admin_visit: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
