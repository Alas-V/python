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


class SupportStatistics:
    @staticmethod
    async def get_support_statistics_optimized(telegram_id: int = None) -> dict:
        async with AsyncSessionLocal() as session:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())

            # Получаем admin_id из telegram_id
            admin_id = None
            if telegram_id:
                admin_query = select(Admin.admin_id).where(
                    Admin.telegram_id == telegram_id
                )
                admin_result = await session.execute(admin_query)
                admin_row = admin_result.scalar_one_or_none()
                admin_id = admin_row if admin_row else None

            # Чистый SQL запрос
            sql_query = text("""
                SELECT 
                    -- Общая статистика
                    COUNT(sa.appeal_id) as total_appeals,
                    
                    -- Статистика за сегодня
                    COUNT(CASE WHEN sa.created_date >= :today_start THEN 1 END) as appeals_today,
                    
                    -- Новые за сегодня (статус NEW)
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'new' THEN 1 END) as new_today,
                    
                    -- В работе за сегодня (статус IN_WORK)
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'in_work' THEN 1 END) as in_work_today,
                    
                    -- Закрытые за сегодня админом
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'closed_by_admin' THEN 1 END) as closed_by_admin_today,
                    
                    -- Закрытые за сегодня пользователем
                    COUNT(CASE WHEN sa.created_date >= :today_start AND sa.status = 'closed_by_user' THEN 1 END) as closed_by_user_today,
                    
                    -- Статистика по приоритетам (только активные - NEW и IN_WORK)
                    COUNT(CASE WHEN sa.priority = 'critical' AND sa.status IN ('new', 'in_work') THEN 1 END) as critical_count,
                    COUNT(CASE WHEN sa.priority = 'high' AND sa.status IN ('new', 'in_work') THEN 1 END) as high_count,
                    COUNT(CASE WHEN sa.priority = 'normal' AND sa.status IN ('new', 'in_work') THEN 1 END) as normal_count,
                    COUNT(CASE WHEN sa.priority = 'low' AND sa.status IN ('new', 'in_work') THEN 1 END) as low_count,
                    
                    -- Общая статистика по закрытым за все время
                    COUNT(CASE WHEN sa.status = 'closed_by_admin' THEN 1 END) as total_closed_by_admin,
                    COUNT(CASE WHEN sa.status = 'closed_by_user' THEN 1 END) as total_closed_by_user,
                    
                    -- Статистика по статусам за все время
                    COUNT(CASE WHEN sa.status = 'new' THEN 1 END) as total_new,
                    COUNT(CASE WHEN sa.status = 'in_work' THEN 1 END) as total_in_work,
                    
                    -- Статистика админа (если передан)
                    COUNT(CASE WHEN sa.assigned_admin_id = :admin_id AND sa.status = 'in_work' THEN 1 END) as admin_active,
                    COUNT(CASE WHEN sa.assigned_admin_id = :admin_id AND sa.status = 'closed_by_admin' THEN 1 END) as admin_closed,
                    COUNT(CASE WHEN sa.assigned_admin_id = :admin_id AND sa.status = 'new' THEN 1 END) as admin_new
                    
                FROM support_appeals sa
            """)

            # Параметры для запроса
            params = {
                "today_start": today_start,
                "admin_id": admin_id
                or 0,  # Если admin_id None, передаем 0 (не найдет совпадений)
            }

            result = await session.execute(sql_query, params)
            row = result.fetchone()

            # Общее количество закрытых за сегодня
            today_closed_total = (row.closed_by_admin_today or 0) + (
                row.closed_by_user_today or 0
            )

            return {
                # Статистика за сегодня
                "new_appeals": row.new_today or 0,
                "today_in_work_appeals": row.in_work_today or 0,
                "today_closed_appeals": today_closed_total,
                "today_closed_by_admin": row.closed_by_admin_today or 0,
                "today_closed_by_user": row.closed_by_user_today or 0,
                "appeals_today": row.appeals_today or 0,
                # Общая статистика
                "all_appeals": row.total_appeals or 0,
                "total_new": row.total_new or 0,
                "total_in_work": row.total_in_work or 0,
                "total_closed_by_admin": row.total_closed_by_admin or 0,
                "total_closed_by_user": row.total_closed_by_user or 0,
                # Статистика по приоритетам
                "critical_appeals": row.critical_count or 0,
                "high_priority_appeals": row.high_count or 0,
                "normal_priority_appeals": row.normal_count or 0,
                "low_priority_appeals": row.low_count or 0,
                # Статистика админа
                "admin_active_appeals": row.admin_active or 0 if admin_id else 0,
                "admin_closed_appeals": row.admin_closed or 0 if admin_id else 0,
                "admin_new_appeals": row.admin_new or 0 if admin_id else 0,
                # Временные метки
                "stats_date": today.strftime("%d.%m.%Y"),
                "generated_at": datetime.now().strftime("%H:%M"),
            }


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
