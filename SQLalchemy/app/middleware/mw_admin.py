from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable
from queries.orm import AdminQueries


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        data["is_admin"] = False
        data["admin_permissions"] = 0
        data["admin_name"] = "Администратор"
        if user_id and not event.from_user.is_bot:
            admin_data = await AdminQueries.get_admin_by_telegram_id(user_id)
            data["is_admin"] = admin_data is not None
            if admin_data:
                data["admin_permissions"] = admin_data.permissions
                data["admin_name"] = admin_data.name
        return await handler(event, data)
