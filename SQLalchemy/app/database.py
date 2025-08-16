from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings
from typing import AsyncIterator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

sync_engine = create_engine(url=settings.sync_database_url, echo=True)
async_engine = create_async_engine(url=settings.async_database_url)  # echo = True

SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine)


class Base(DeclarativeBase):
    pass


async def get_async_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_version():
    async with async_engine.connect() as conn:
        res = await conn.execute(text("SELECT VERSION()"))
        print(f"{res.all()=}")
        conn.commit


# first , all - не оптимизируют запрос , данные и так хранятся в оперативке
# сырой запрос через text(...) эффективнее , но не всегда нужна такая эффективность
