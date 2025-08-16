from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from models import Base, Author, Book, Review, User
from database import engine, session_local
from schemas import (
    AuthorCreate,
    AuthorResponse,
    BookCreate,
    BookResponse,
    ReviewCreate,
    ReviewResponse,
    UserCreate,
    UserResponse,
)

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = session_local()
    try:
        yield db
    except:
        db.rollback()
        raise
    finally:
        db.close()


@app.post("/authors_post/", response_model=AuthorResponse)
async def create_author(
    author: AuthorCreate, db: Session = Depends(get_db)
) -> AuthorResponse:
    db_author = Author(name=author.name, country=author.country)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


@app.get("/authors_get/", response_model=List[AuthorResponse])
async def get_authors(db: Session = Depends(get_db)):
    return db.query(Author).all()


@app.get("/authors/{author_id}/books/", response_model=List[BookResponse])
async def get_authors_books(author_id: int, db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.author_id == author_id).all()
    if not books:
        raise HTTPException(status_code=404, detail="Page not found")
    return books


@app.post("/books_post/", response_model=BookResponse)
async def post_book(book: BookCreate, db: Session = Depends(get_db)) -> BookResponse:
    author = db.query(Author).filter(Author.id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Page not found")
    db_book = Book(title=book.title, year=book.year, author_id=book.author_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.get("/books_get/", response_model=List[BookResponse])
async def get_all_books(db: Session = Depends(get_db)):
    return db.query(Book).all()


@app.get("/books")
async def get_books_by_rating(
    min_rating: Optional[float] = None, db: Session = Depends(get_db)
):
    books = (
        db.query(Book).options(joinedload(Book.reviews), joinedload(Book.author)).all()
    )
    book_responses = [BookResponse.from_orm(b) for b in books]
    if min_rating is not None:
        book_responses = [
            b for b in book_responses if b.rating and b.rating >= min_rating
        ]

    if not book_responses:
        raise HTTPException(
            status_code=404, detail=f"No books with rating >= {min_rating}"
        )
    return book_responses


@app.post("/books/{book_id}/rate")
async def new_review(review: ReviewCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == review.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Page not found")
    db_review = Review(
        book_id=review.book_id,
        rating=review.rating,
        title=review.title,
        body=review.body,
        user_id=review.user_id,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.post("/users_create/", response_model=UserResponse)
async def user_create(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, age=user.age, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/books/{book_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(book_id: int, db: Session = Depends(get_db)):
    all_reviews = db.query(Review).filter(Review.book_id == book_id).all()
    if all_reviews is None:
        raise HTTPException(
            status_code=404, detail="Page not found. This book has no reviews."
        )
    return all_reviews
