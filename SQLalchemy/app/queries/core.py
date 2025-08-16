from database import Base, async_engine
from sqlalchemy import insert, select, update, text
from sqlalchemy.exc import SQLAlchemyError
from models import Author, Book, User


async def select_books():
    async with async_engine.connect() as conn:
        query = select(Book)
        result = await conn.execute(query)
        books = result.all()
        print(f"{books}")


async def update_user_name(user_id: int, new_user_name: str):
    async with async_engine.connect() as conn:
        stmt = text("UPDATE users SET user_name=:up_user_name WHERE user_id=:id")
        stmt = stmt.bindparams(up_user_name=new_user_name, id=user_id)
        await conn.execute(stmt)
        await conn.commit()


async def update_username(user_id: int, new_user_name: str):
    async with async_engine.connect() as conn:
        stmt = update(User).values(user_name=new_user_name).filter_by(user_id=user_id)
        await conn.execute(stmt)
        await conn.commit()


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def insert_data_author(author_data):
    try:
        async with async_engine.connect() as conn:
            stmt = insert(Author).values(**author_data.model_dump())
            await conn.execute(stmt)
            await conn.commit()
    except SQLAlchemyError as e:
        print(f"DB Error! {e}")
        raise


# async def insert_data(name, country):
#     async with async_engine.connect() as conn:
#         stmt = """
#         INSERT INTO authors (name, country)
#         VALUES (:name, :country)
#         """
#         authors = [
#             {"name": name, "country": country},
#         ]
#         await conn.execute(text(stmt), authors)
#         await conn.commit()
