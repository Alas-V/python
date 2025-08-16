from pydantic import BaseModel, ConfigDict, Field, EmailStr, SecretStr, computed_field
from typing import Annotated, Optional
from datetime import datetime
from enum import Enum

present_year = datetime.now().year


class BookStatus(Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    LOST = "lost"


class AuthorBase(BaseModel):
    author_name: Annotated[str, Field(title="Author name", min_length=2, max_length=90)]
    author_country: Annotated[
        str, Field(title="Author's country", min_length=3, max_length=80)
    ]


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    author_id: Annotated[int, Field(title="Author's id")]
    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    book_title: Annotated[str, Field(title="Title of the book", max_length=50)]
    book_year: Annotated[int, Field(title="Year of book publishing", le=present_year)]
    reviews: Annotated[list, Field(title="All reviews for book")] = None
    author_id: Annotated[int, Field(title="Author of the book")]
    book_status: Annotated[Optional[BookStatus], Field(title="Status of the book")] = (
        None
    )
    book_price: Annotated[int, Field(title="Book price", gt=0)]


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    book_id: Annotated[int, Field(title="Book id")]
    reviews: list["ReviewResponse"]
    book_status: BookStatus

    @computed_field
    @property
    def rating(self) -> float | None:
        if not self.reviews:
            return None
        return round(sum(r.review_rating for r in self.reviews) / len(self.reviews), 1)

    author: Annotated[AuthorResponse, Field(title="Author of the book")]
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    user_name: Annotated[str, Field(title="User's name", min_length=3, max_length=20)]
    user_age: Annotated[int, Field(title="User's age", gt=14, le=120)]


class UserCreate(UserBase):
    user_email: Annotated[EmailStr, Field(title="User's email and auto validation")]
    password: Annotated[SecretStr, Field(title="User's password, auto hiding in logs")]


class UserResponse(UserBase):
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    user_name: Annotated[Optional[str], Field(min_length=3, max_length=20)] = None
    user_age: Annotated[Optional[int], Field(gt=14, le=120)] = None
    model_config = ConfigDict(extra="forbid")


class ReviewBase(BaseModel):
    book_id: Annotated[int, Field(title="On which book is this review (id)", gt=0)]
    review_rating: Annotated[int, Field(title="Rating of the book 1-5", ge=1, le=5)]
    review_title: Annotated[str, Field(title="Title of the review", max_length=100)]
    review_body: Annotated[
        str, Field(title="Review body", min_length=2, max_length=1000)
    ]
    user_id: Annotated[int, Field(title="Id of the User that made a review")]
    # created_at: Annotated[datetime, Field(title="When review was created")]


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    user: Annotated[UserResponse, Field(title="User, that wrote a review")]
    # book: Annotated[BookResponse, Field(Title="On witch book was that review")]
    model_config = ConfigDict(from_attributes=True)
