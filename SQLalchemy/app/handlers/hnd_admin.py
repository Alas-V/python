from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
import asyncio

admin_router = Router()


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


@admin_router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    telegram_id = int(callback.from_user.id)
    await AdminQueries.check_admin(telegram_id)
