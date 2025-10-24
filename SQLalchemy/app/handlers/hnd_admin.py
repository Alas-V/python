from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from middleware.mw_admin import AdminMiddleware
from keyboards.kb_admin import KbAdmin
from keyboards.kb_support import SupportKeyboards
from queries.orm import AdminQueries, SupportQueries
from functools import wraps
from typing import Union
from text_templates import (
    admin_personal_support_statistic,
    admin_appeal_split_messages,
    admin_message_rules,
)
from utils.states import AdminSupportState
from models import AppealStatus
import asyncio

admin_router = Router()
admin_router.callback_query.middleware(AdminMiddleware())
admin_router.message.middleware(AdminMiddleware())


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            # await asyncio.sleep(0.1)
        except Exception as e:
            if "message to delete not found" not in str(
                e
            ) and "message can't be deleted" not in str(e):
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
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", [])
    last_hint_id = data.get("last_hint_id")
    main_message = data.get("main_message")
    if messages_to_delete:
        await delete_messages(
            callback.bot, callback.message.chat.id, messages_to_delete
        )
    if last_hint_id:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception:
            pass
    await state.clear()
    statistic_data = await AdminQueries.get_admin_support_statistics(
        telegram_id=int(callback.from_user.id)
    )
    if "error" in statistic_data:
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)
        return
    text = await admin_personal_support_statistic(statistic_data)
    if main_message:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=main_message,
            text=text,
            reply_markup=await KbAdmin.support_main_keyboard(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        text, reply_markup=await KbAdmin.support_main_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "support_my_active")
@admin_required
async def active_supports(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    admin_tg_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(admin_tg_id)
    appeals_in_work = await AdminQueries.appeal_in_work_for_kb(admin_id=admin.admin_id)
    if not appeals_in_work:
        await callback.answer("У вас сейчас нет активных обращений в поддержку")
        return
    main_message = await callback.message.edit_text(
        text="Выберите одно из Ваших активных обращений в поддержку:",
        reply_markup=await KbAdmin.kb_my_active_appeals(appeals_in_work),
    )
    await state.update_data(
        main_message_id=main_message.message_id,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_open_appeal_"))
@admin_required
async def admin_open_appeal(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    appeal_id = int(callback.data.split("_")[3])
    appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
    await AdminQueries.admin_visited(appeal_id)
    message_parts, main_text = await admin_appeal_split_messages(appeal, admin_name)
    messages_to_delete = []
    await callback.message.delete()
    if not message_parts:
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(appeal_id),
            parse_mode="Markdown",
        )
        messages_to_delete.append(main_message.message_id)
    else:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await callback.message.answer(part_text, parse_mode="Markdown")
            messages_to_delete.append(msg.message_id)
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(appeal_id),
            parse_mode="Markdown",
        )
    await state.update_data(
        messages_to_delete=messages_to_delete,
        main_message_id=main_message.message_id,
        current_step="in_appeal",
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
    await AdminQueries.admin_visited(new_appeal.appeal_id)
    message_parts, main_text = await admin_appeal_split_messages(new_appeal, admin_name)
    messages_to_delete = []
    await callback.message.delete()
    if not message_parts:
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                new_appeal.appeal_id
            ),
            parse_mode="Markdown",
        )
        messages_to_delete.append(main_message.message_id)
    else:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await callback.message.answer(part_text, parse_mode="Markdown")
            messages_to_delete.append(msg.message_id)
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                new_appeal.appeal_id
            ),
            parse_mode="Markdown",
        )
    await state.update_data(
        appeal_id=new_appeal.appeal_id,
        messages_to_delete=messages_to_delete,
        main_message_id=main_message.message_id,
        user_telegram_id=new_appeal.telegram_id,
        current_step="in_support",
    )
    await callback.answer(f"✅ Обращение #{new_appeal.appeal_id} взято в работу")


@admin_router.callback_query(F.data.startswith("admin_support_reply_"))
@admin_required
async def admin_reply(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    bot = callback.message.bot
    data = await state.get_data()
    appeal_id = int(callback.data.split("_")[3])
    appeal_status = await SupportQueries.check_appeal_status(appeal_id)
    if (
        appeal_status == AppealStatus.CLOSED_BY_ADMIN
        or appeal_status == AppealStatus.CLOSED_BY_USER
    ):
        dict_for_text = {
            "closed_by_user": "пользователем",
            "closed_by_admin": "администратором",
        }
        await callback.answer(
            text=f"Вы не можете отправить новое сообщение, так как обращение уже было закрыто {dict_for_text[appeal_status]} ",
            show_alert=True,
        )
        await callback.answer()
        return

    hint_message = await callback.message.answer(
        text="📝 Отправьте сообщение ниже, чтобы ответить пользователю"
    )
    current_messages_to_delete = data.get("messages_to_delete", [])
    current_main_message_id = data.get("main_message_id")
    await state.set_state(AdminSupportState.message_from_support)
    await state.update_data(
        appeal_id=appeal_id,
        last_hint_id=hint_message.message_id,
        messages_to_delete=current_messages_to_delete,
        main_message_id=current_main_message_id,
        admin_name=admin_name,
    )


# admin_main_stats
# admin_main_orders
# admin_main_control_books
# admin_main_control_admins


# FMScontext hnd
@admin_router.message(AdminSupportState.message_from_support, F.text)
@admin_required
async def message_from_support(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    bot = message.bot
    data = await state.get_data()
    appeal_id = data["appeal_id"]
    last_hint_id = data.get("last_hint_id")
    old_messages_to_delete = data.get("messages_to_delete", [])
    old_main_message_id = data.get("main_message_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить подсказку: {e}")
    admin = await AdminQueries.get_admin_by_telegram_id(message.from_user.id)
    if not admin:
        await message.answer("❌ Администратор не найден")
        await state.clear()
        return
    await AdminQueries.admin_support_to_user(admin.admin_id, appeal_id, message.text)
    appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
    if appeal and appeal.user:
        try:
            await bot.send_message(
                chat_id=appeal.telegram_id,
                text=f"🛠 *Ответ службы поддержки:*\n\n{message.text}\n\n— {admin_name}",
                parse_mode="Markdown",
                reply_markup=await SupportKeyboards.open_appel(appeal_id),
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю: {e}")
    all_messages_to_delete = old_messages_to_delete.copy()
    if old_main_message_id:
        all_messages_to_delete.append(old_main_message_id)
    for msg_id in all_messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")
    updated_appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
    if not updated_appeal:
        await message.answer("❌ Обращение не найдено")
        await state.clear()
        return
    message_parts, main_text = await admin_appeal_split_messages(
        updated_appeal, admin_name
    )
    new_messages_to_delete = []
    if message_parts:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await message.answer(part_text, parse_mode="Markdown")
            new_messages_to_delete.append(msg.message_id)
    main_message = await message.answer(
        text=main_text,
        reply_markup=await KbAdmin.support_appeal_actions_keyboard(appeal_id),
        parse_mode="Markdown",
    )
    hint_message = await message.answer("✅ Ваше сообщение отправлено пользователю")
    await state.update_data(
        last_hint_id=hint_message.message_id,
        messages_to_delete=new_messages_to_delete,
        main_message_id=main_message.message_id,
    )
    # await state.clear()
