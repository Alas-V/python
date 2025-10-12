from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from middleware.mw_admin import AdminMiddleware
from keyboards.kb_admin import KbAdmin
import asyncio

admin_router = Router()
admin_router.message.middleware(AdminMiddleware())
admin_router.callback_query.middleware(AdminMiddleware())


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


@admin_router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, data: dict):
    if not data.get("is_admin"):
        await callback.answer("❌ У вас нет доступа к админ-панели", show_alert=True)
        return
    await callback.message.edit_text(
        "👑 Админ-панель\n\nВыберите раздел:",
        reply_markup=await KbAdmin.admin_main_keyboard(),
    )
