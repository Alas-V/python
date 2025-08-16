from pydantic import BaseModel, ConfigDict, Field, EmailStr, SecretStr, computed_field
from typing import Annotated
from datetime import datetime

present_year = datetime.now().year


class AuthorBase(BaseModel):
    name: Annotated[
        str,
        Field(
            title="Author name",
            min_length=2,
            max_length=30,
        ),
    ]
    country: Annotated[
        str,
        Field(
            title="Author's country",
            min_length=3,
            max_length=30,
        ),
    ]


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    id: Annotated[
        int,
        Field(
            title="Author's id",
        ),
    ]
    model_config = ConfigDict(
        from_attributes=True,
    )


class BookBase(BaseModel):
    title: Annotated[
        str,
        Field(
            title="Title of the book",
            max_length=30,
        ),
    ]
    year: Annotated[
        int,
        Field(
            title="Year of book publishing",
            le=present_year,
        ),
    ]
    reviews: Annotated[list, Field(title="All reviews for book")] = None
    author_id: Annotated[
        int,
        Field(
            title="Author of the book",
        ),
    ]


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: Annotated[
        int,
        Field(
            title="Book id",
        ),
    ]
    reviews: list["ReviewResponse"]

    @computed_field
    @property
    def rating(self) -> float | None:
        if not self.reviews:
            return None
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    author: Annotated[
        AuthorResponse,
        Field(
            title="Author of the book",
        ),
    ]
    model_config = ConfigDict(
        from_attributes=True,
    )


class UserBase(BaseModel):
    username: Annotated[
        str,
        Field(
            title="User's name",
            min_length=3,
            max_length=20,
        ),
    ]
    age: Annotated[
        int,
        Field(
            title="User's age",
            gt=14,
            le=120,
        ),
    ]


class UserCreate(UserBase):
    email: Annotated[EmailStr, Field(title="User's email and auto validation")]
    password: Annotated[SecretStr, Field(title="User's password, auto hiding in logs")]


class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(
        from_attributes=True,
    )


class ReviewBase(BaseModel):
    book_id: Annotated[int, Field(title="On which book is this review (id)", gt=0)]
    rating: Annotated[
        int,
        Field(
            title="Rating of the book 1-5",
            ge=1,
            le=5,
        ),
    ]
    title: Annotated[
        str,
        Field(
            title="Title of the review",
            max_length=30,
        ),
    ]
    body: Annotated[
        str,
        Field(
            title="Review body",
            min_length=2,
            max_length=600,
        ),
    ]
    user_id: Annotated[int, Field(title="Id of the User that made a review")]


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    user: Annotated[UserResponse, Field(title="User, that wrote a review")]
    # book: Annotated[BookResponse, Field(Title="On witch book was that review")]
    model_config = ConfigDict(
        from_attributes=True,
    )
