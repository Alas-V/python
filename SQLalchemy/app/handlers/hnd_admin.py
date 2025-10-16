from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from middleware.mw_admin import AdminMiddleware
from keyboards.kb_admin import KbAdmin
from queries.orm import AdminQueries
from functools import wraps
from typing import Union
from text_templates import (
    admin_personal_support_statistic,
    admin_appeal_split_messages,
    admin_message_rules,
)
from utils.states import AdminSupportState
import asyncio

admin_router = Router()
admin_router.callback_query.middleware(AdminMiddleware())
admin_router.message.middleware(AdminMiddleware())


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            if "message to delete not found" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


def admin_required(handler):
    @wraps(handler)
    async def wrapper(event: Union[Message, CallbackQuery], *args, **kwargs):
        is_admin = kwargs.get("is_admin", False)
        if not is_admin:
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ У вас нет доступа к админ-панели", show_alert=True
                )
            elif isinstance(event, Message):
                await event.answer("❌ У вас нет доступа к админ-панели")
            return
        return await handler(event, *args, **kwargs)

    return wrapper


@admin_router.callback_query(F.data == "admin_menu")
@admin_required
async def admin_menu(
    callback: CallbackQuery, is_admin: bool, admin_permissions: int, admin_name: str
):
    await callback.message.edit_text(
        f"👑 Добрый день, {admin_name}!\nАдмин-панель\n\nВыберите раздел:",
        reply_markup=await KbAdmin.admin_main_keyboard(admin_permissions),
    )


@admin_router.callback_query(F.data == "admin_main_support")
@admin_required
async def my_support_statistics(
    callback: CallbackQuery, is_admin: bool, admin_permissions: int, admin_name: str
):
    statistic_data = await AdminQueries.get_admin_support_statistics(
        telegram_id=int(callback.from_user.id)
    )
    if "error" in statistic_data:
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)
        return
    text = await admin_personal_support_statistic(statistic_data)
    await callback.message.edit_text(
        text, reply_markup=await KbAdmin.support_main_keyboard()
    )


@admin_router.callback_query(F.data == "agreement_before_new_appeal")
@admin_required
async def agreement_before_new_appeal(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    new_appeal = await AdminQueries.get_new_appeal()
    if not new_appeal:
        await callback.answer("Сейчас нет новых обращений", show_alert=True)
        return
    agreement = await admin_message_rules()
    await callback.message.edit_text(
        text=agreement,
        parse_mode="Markdown",
        reply_markup=await KbAdmin.admin_agreement(),
    )


@admin_router.callback_query(F.data == "support_take_new")
@admin_required
async def support_take_new(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    new_appeal = await AdminQueries.get_new_appeal()
    if not new_appeal:
        await callback.answer("Сейчас нет новых обращений", show_alert=True)
        return
    await AdminQueries.assign_appeal_to_admin(
        int(new_appeal.appeal_id), int(callback.from_user.id)
    )
    message_parts, main_text = await admin_appeal_split_messages(new_appeal, admin_name)
    messages_to_delete = []
    if not message_parts:
        await callback.message.edit_text(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                new_appeal.appeal_id
            ),
            parse_mode="Markdown",
        )
    else:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await callback.message.answer(part_text, parse_mode="Markdown")
            messages_to_delete.append(msg.message_id)
        await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                new_appeal.appeal_id
            ),
            parse_mode="Markdown",
        )
    await callback.answer(f"✅ Обращение #{new_appeal.appeal_id} взято в работу")
    # await state.set_state(AdminSupportState.message_from_support)


# admin_main_stats
# admin_main_orders
# admin_main_control_books
# admin_main_control_admins
