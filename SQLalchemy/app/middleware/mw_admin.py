from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from config import ADMIN_IDS
from queries.orm import AdminQueries
import datetime


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        admin_data = await AdminQueries.get_admin_by_telegram_id(user_id)
        data["is_admin"] = admin_data is not None
        data["admin_permissions"] = admin_data.permissions if admin_data else 0
        data["admin_data"] = admin_data
        result = await handler(event, data)
        return result
