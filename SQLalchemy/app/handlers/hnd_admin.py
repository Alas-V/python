from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from middleware.mw_admin import AdminMiddleware
from keyboards.kb_admin import KbAdmin
from keyboards.kb_support import SupportKeyboards
from keyboards.kb_order import OrderProcessing
from queries.orm import (
    AdminQueries,
    SupportQueries,
    StatisticsQueries,
    BookQueries,
    OrderQueries,
)
from functools import wraps
from typing import Union
from text_templates import (
    admin_personal_support_statistic,
    admin_appeal_split_messages,
    admin_message_rules,
    admin_all_statistic_text,
    admin_order_statistic,
    admin_format_order_details,
)
from utils.states import AdminSupportState, AdminOrderState, AdminReasonToCancellation
from models import AppealStatus, AdminPermission, OrderStatus
import asyncio
from aiogram.exceptions import TelegramBadRequest
from utils.admin_utils import PermissionChecker


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
            continue


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


async def send_user_msg(
    bot: Bot,
    order_id: int,
    user_tg_id: int,
    status: OrderStatus,
    reason_to_cancellation=None,
) -> bool:
    try:
        status_messages = {
            OrderStatus.PROCESSING: "🔄 Ваш заказ взят в обработку",
            OrderStatus.DELIVERING: "🚚 Ваш заказ передан в доставку",
            OrderStatus.COMPLETED: "✅ Ваш заказ успешно доставлен",
            OrderStatus.CANCELLED: "❌ К сожалению, Ваш заказ был отменен, по причине: ",
        }
        message_text = (
            f"📦 *Статус вашего заказа обновлён!*\n\n🆔 Номер заказа: *{order_id}*\n"
        )
        if status == OrderStatus.CANCELLED:
            message_text += (
                f"📊 Статус: *{status}*\n\n"
                f"{status_messages.get(status, '')}\n{reason_to_cancellation}\n"
                f"💰 Деньги за заказ были возвращены на Ваш счет внутри бота"
                f"\n📨 При необходимости Вы можете обратиться в нашу службу поддержки"
            )
        elif status == OrderStatus.DELIVERING:
            message_text += (
                f"📊 Статус: *{status}*\n\n"
                f"{status_messages.get(status, '')}\n\n"
                f"📱 Следить за статусом заказа можно в разделе «Мои заказы»"
            )
        elif status == OrderStatus.COMPLETED:
            message_text += (
                f"📊 Статус: *{status}*\n\n"
                f"{status_messages.get(status, '')}\n{reason_to_cancellation}\n"
                f"need text here "
            )
        await bot.send_message(
            chat_id=user_tg_id,
            text=message_text,
            parse_mode="Markdown",
            reply_markup=await OrderProcessing.kb_open_order_user(order_id, status),
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки уведомления пользователю {user_tg_id}: {e}")
        return False


@admin_router.callback_query(F.data == "admin_menu")
@admin_required
async def admin_menu(
    callback: CallbackQuery, is_admin: bool, admin_permissions: int, admin_name: str
):
    await callback.message.edit_text(
        f"👑 Добрый день, {admin_name}!\nАдмин-панель\n\nВыберите раздел:",
        reply_markup=await KbAdmin.admin_main_keyboard(admin_permissions),
    )


@admin_router.callback_query(F.data.startswith("admin_appeal_close_"))
@admin_required
async def admin_appeal_close(
    callback: CallbackQuery, is_admin: bool, admin_permissions: int, admin_name: str
):
    appeal_id = int(callback.data.split("_")[3])
    await callback.message.edit_text(
        text="Вы уверены что хотите закрыть это обращение?\nПользователи могут создавать обращения только раз в 60 минут❗ \n\n(Закрытое ранее обращения нельзя открывать заново)",
        reply_markup=await KbAdmin.sure_close(appeal_id),
    )


@admin_router.callback_query(F.data.startswith("admin_appeal_sure_close_"))
@admin_required
async def appeal_sure_close(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", [])
    last_hint_id = data.get("last_hint_id")
    main_message_id = data.get("main_message_id")
    all_messages_to_delete = messages_to_delete.copy()
    if main_message_id and main_message_id not in all_messages_to_delete:
        all_messages_to_delete.append(main_message_id)
    if all_messages_to_delete:
        await delete_messages(
            callback.bot, callback.message.chat.id, all_messages_to_delete
        )
    if last_hint_id:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception:
            pass
    await state.clear()
    appeal_id = int(callback.data.split("_")[4])
    await SupportQueries.close_appeal(appeal_id, who_close="admin")
    status = await SupportQueries.check_appeal_status(appeal_id)
    appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
    message_parts, main_text = await admin_appeal_split_messages(appeal, admin_name)
    try:
        await callback.message.delete()
    except Exception:
        pass
    new_messages_to_delete = []
    if not message_parts:
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                appeal_id, status
            ),
            parse_mode="Markdown",
        )
        new_messages_to_delete.append(main_message.message_id)
    else:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await callback.message.answer(part_text, parse_mode="Markdown")
            new_messages_to_delete.append(msg.message_id)
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                appeal_id, status
            ),
            parse_mode="Markdown",
        )
        new_messages_to_delete.append(main_message.message_id)
    await state.update_data(
        messages_to_delete=new_messages_to_delete,
        main_message_id=main_message.message_id,
        current_step="in_appeal",
    )
    await callback.answer("✅ Обращение закрыто")


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
    main_message_id = data.get("main_message_id")
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
    statistic_data = await StatisticsQueries.get_admin_support_statistics(
        telegram_id=int(callback.from_user.id)
    )
    if "error" in statistic_data:
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)
        return
    text = await admin_personal_support_statistic(statistic_data)
    if main_message_id:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=main_message_id,
                text=text,
                reply_markup=await KbAdmin.support_main_keyboard(),
            )
            await callback.answer()
            return
        except TelegramBadRequest:
            pass
    try:
        await callback.message.edit_text(
            text, reply_markup=await KbAdmin.support_main_keyboard()
        )
    except TelegramBadRequest:
        await callback.message.answer(
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
    status = await SupportQueries.check_appeal_status(appeal_id)
    message_parts, main_text = await admin_appeal_split_messages(appeal, admin_name)
    messages_to_delete = []
    await callback.message.delete()
    if not message_parts:
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                appeal_id, status
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
                appeal_id, status
            ),
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
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    appeals_count = await AdminQueries.count_appeals_in_work(admin.admin_id)
    if appeals_count == 100:
        await callback.answer(
            "Вы не можете взять одновременно больше 10 обращений в работу ",
            show_alert=True,
        )
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
    status = await SupportQueries.check_appeal_status(new_appeal.appeal_id)
    message_parts, main_text = await admin_appeal_split_messages(new_appeal, admin_name)
    messages_to_delete = []
    await callback.message.delete()
    if not message_parts:
        main_message = await callback.message.answer(
            text=main_text,
            reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                new_appeal.appeal_id, status
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
                new_appeal.appeal_id, status
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
            show_alert=True,
            text=f"Вы не можете отправить новое сообщение, так как обращение уже было закрыто {dict_for_text[appeal_status]} ",
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


@admin_router.callback_query(F.data == "support_my_closed")
@admin_required
async def support_my_close(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    await callback.message.edit_text(
        text="Выберите способ поиска Ваших закрытых обращений ",
        reply_markup=await KbAdmin.kb_closed_main_menu(),
    )


@admin_router.callback_query(F.data == "admin_last_appeals")
@admin_required
async def admin_last_appeals(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    has_closed_appeals = await AdminQueries.has_closed_appeals(admin.admin_id)
    if not has_closed_appeals:
        callback.answer(text="У вас нет закрытых обращений", show_alert=True)
        return
    appeals_data, total_count = await AdminQueries.get_closed_appeals(admin.admin_id)
    await callback.message.edit_text(
        text=f"Ваши закрытые обращения. Всего у вас {total_count} закрытых обращений ",
        reply_markup=await KbAdmin.universal_appeals_keyboard(
            appeals_data=appeals_data, total_count=total_count
        ),
    )


@admin_router.callback_query(F.data.startswith("admin_all_closed_appeals_page_"))
@admin_required
async def admin_all_closed_appeals_pagination(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    page = int(callback.data.split("_")[-1])
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    appeals_data, total_count = await AdminQueries.get_closed_appeals(
        admin.admin_id, page=page
    )
    await callback.message.edit_text(
        text=f"Ваши закрытые обращения. Всего у вас {total_count} закрытых обращений",
        reply_markup=await KbAdmin.universal_appeals_keyboard(
            appeals_data=appeals_data, page=page, total_count=total_count
        ),
    )


@admin_router.callback_query(F.data == "admin_closed_find_by_appeal_id")
@admin_required
async def admin_closed_find_by_appeal_id(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    has_closed_appeals = await AdminQueries.has_closed_appeals(admin.admin_id)
    if not has_closed_appeals:
        has_admin_permission = PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_ADMINS
        )
        if not has_admin_permission:
            callback.answer(text="У вас нет закрытых обращений", show_alert=True)
            return
    main_message = await callback.message.edit_text(
        text="Напишите номер обращения: ",
        reply_markup=await KbAdmin.go_back_to_find_filters(),
    )
    await state.set_state(AdminSupportState.sending_appeal_id_for_find)
    await state.update_data(main_message_id=main_message.message_id)


@admin_router.callback_query(F.data == "admin_find_by_username")
@admin_required
async def admin_find_by_username(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    has_closed_appeals = await AdminQueries.has_closed_appeals(admin.admin_id)
    if not has_closed_appeals:
        has_admin_permission = PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_ADMINS
        )
        if not has_admin_permission:
            callback.answer(text="У вас нет закрытых обращений", show_alert=True)
            return
    main_message = await callback.message.edit_text(
        text="Напишите username пользователя для просмотра его обращений: @...",
        reply_markup=await KbAdmin.go_back_to_find_filters(),
    )
    await state.set_state(AdminSupportState.sending_username_for_find)
    await state.update_data(main_message_id=main_message.message_id)


@admin_router.callback_query(F.data.startswith("search_username_page_"))
@admin_required
async def search_username_pagination(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    page = int(callback.data.split("_")[-1])
    data = await state.get_data()
    username = data.get("search_username")
    if not username:
        await callback.answer("Ошибка поиска", show_alert=True)
        return
    telegram_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    has_admin_permission = PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    )
    appeals_data, total_count = await AdminQueries.get_appeals_by_username(
        username=username,
        admin_id=admin.admin_id,
        has_admin_permission=has_admin_permission,
        page=page,
        items_per_page=10,
    )
    if not appeals_data:
        await callback.answer("Больше обращений нет", show_alert=True)
        return
    await callback.message.edit_text(
        text=f"📋 Обращения пользователя @{username} (найдено: {total_count}):",
        reply_markup=await KbAdmin.universal_appeals_keyboard(
            appeals_data=appeals_data,
            page=page,
            total_count=total_count,
            callback_prefix="admin_open_appeal",
            page_callback="search_username_page",
            back_callback="support_my_closed",
            items_per_page=10,
        ),
    )
    await state.update_data(current_page=page)


@admin_router.callback_query(F.data == "admin_main_stats")
@admin_required
async def admin_statistics(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.VIEW_STATS
    ):
        await callback.answer(
            "❌ У вас нет прав для просмотра статистики", show_alert=True
        )
        return
    try:
        stats = await StatisticsQueries.get_comprehensive_stats()
        text = await admin_all_statistic_text(stats)
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.in_admin_statistic(),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in admin_statistics: {e}")
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)


@admin_router.callback_query(F.data == "admin_main_orders")
@admin_required
async def admin_main_orders(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ORDERS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления заказами", show_alert=True
        )
        return
    try:
        order_stats = await StatisticsQueries.orders_statistic()
        if "error" in order_stats:
            await callback.message.edit_text(
                "❌ Ошибка при получении статистики заказов",
                reply_markup=await KbAdmin.kb_admin_main_order(admin_permissions),
            )
            return
        text = admin_order_statistic(order_stats)
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.kb_admin_main_order(admin_permissions),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in admin_main_orders: {e}")
        await callback.answer(
            "❌ Ошибка при получении статистики заказов", show_alert=True
        )


@admin_router.callback_query(F.data.startswith("admin_orders_"))
@admin_required
async def admin_orders(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    order_type = str(callback.data.split("_")[-1])
    try:
        page = 0
        total_count = await AdminQueries.get_admin_orders_count(order_type)
        orders_data = await AdminQueries.get_admin_orders_paginated(
            order_type, page=page
        )
        if not orders_data:
            await callback.answer(
                text="❌ Нет заказов",
                show_alert=True,
            )
            return
        order_type_text = {
            "new": f"🆕 <b>Новые заказы</b>\n\n📋 Найдено новых заказов: {total_count}",
            "delivering": f"🚚 <b>Заказы в доставке</b>\n\n📋 Найдено заказов в доставке: {total_count}",
            "completed": f"📫 <b>Доставленные заказы</b>\n\n📋 Найдено доставленных заказов: {total_count}",
            "canceled": f"❌ <b>Отменённые заказы</b>\n\n📋 Найдено отменённых заказов: {total_count}",
        }
        await callback.message.edit_text(
            text=order_type_text.get(order_type),
            reply_markup=await KbAdmin.kb_admin_find_orders(
                order_type, orders_data=orders_data, page=page, total_count=total_count
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in admin_new_orders: {e}")
        await callback.answer("❌ Ошибка при загрузке новых заказов", show_alert=True)


@admin_router.callback_query(F.data.startswith("page_admin_orders_"))
@admin_required
async def admin_new_orders_pagination(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    try:
        page = int(callback.data.split("_")[-1])
        order_type = str(callback.data.split("_")[-2])
        total_count = await AdminQueries.get_admin_orders_count(order_type)
        orders_data = await AdminQueries.get_admin_orders_paginated(
            order_type, page=page
        )
        if not orders_data:
            await callback.answer("Больше заказов нет", show_alert=True)
            return
        order_type_text = {
            "new": f"🆕 <b>Новые заказы</b>\n\n📋 Найдено новых заказов: {total_count}",
            "delivering": f"🚚 <b>Заказы в доставке</b>\n\n📋 Найдено заказов в доставке: {total_count}",
            "completed": f"📫 <b>Доставленные заказы</b>\n\n📋 Найдено доставленных заказов: {total_count}",
            "canceled": f"❌ <b>Отменённые заказы</b>\n\n📋 Найдено отменённых заказов: {total_count}",
        }
        await callback.message.edit_text(
            text=order_type_text.get(order_type),
            reply_markup=await KbAdmin.kb_admin_find_orders(
                order_type, orders_data=orders_data, page=page, total_count=total_count
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in admin_new_orders_pagination: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_view_order_"))
@admin_required
async def admin_view_order(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    try:
        order_id = int(callback.data.split("_")[-1])
        order_details = await AdminQueries.get_order_details(order_id)
        if not order_details:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
        text = await admin_format_order_details(order_details)
        status = await AdminQueries.get_order_status(order_id)
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.kb_order_actions(
                order_id, admin_permissions, status
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in admin_view_order: {e}")
        await callback.answer("❌ Ошибка при загрузке заказа", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_order_status_"))
@admin_required
async def admin_order_status_completed(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    order_id = int(callback.data.split("_")[-1])
    status = callback.data.split("_")[-2]
    if status == "completed":
        await callback.message.edit_text(
            text=f"Вы завершаете доставку заказа №{order_id}",
            reply_markup=await KbAdmin.sure_to_change_status(order_id, status),
        )
        return
    elif status == "delivering":
        await callback.message.edit_text(
            text=f"Вы передаете заказ №{order_id} в доставку",
            reply_markup=await KbAdmin.sure_to_change_status(order_id, status),
        )
        return
    elif status == "cancelled":
        await callback.message.edit_text(
            text=f"Вы уверены что хотите отменить заказ №{order_id}",
            reply_markup=await KbAdmin.sure_to_change_status(order_id, status),
        )
        return


@admin_router.callback_query(F.data.startswith("sure_change_status_"))
@admin_required
async def sure_change_status(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    status_dict = {
        "processing": OrderStatus.PROCESSING,
        "delivering": OrderStatus.DELIVERING,
        "completed": OrderStatus.COMPLETED,
        "cancelled": OrderStatus.CANCELLED,
    }
    parts = callback.data.split("_")
    order_id = int(parts[-2])
    new_status_key = parts[-1]
    status = status_dict.get(new_status_key)
    if not status:
        await callback.answer("❌ Неизвестный статус", show_alert=True)
        return
    order_updated = await AdminQueries.get_order_new_status(order_id, status)
    if order_updated:
        order_data = await AdminQueries.get_order_details(order_id)
        if not order_data:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
        user_info = order_data.get("user", {})
        user_tg_id = user_info.get("telegram_id")
        text = await admin_format_order_details(order_data)
        await callback.answer("✅ Статус заказа изменен!", show_alert=True)
        if user_tg_id:
            send_msg_to_user = await send_user_msg(bot, order_id, user_tg_id, status)
            if not send_msg_to_user:
                await callback.answer(
                    "⚠️ Статус изменен, но не удалось уведомить пользователя",
                    show_alert=True,
                )
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.kb_order_actions(
                order_id, admin_permissions, status
            ),
            parse_mode="HTML",
        )
        return
    await callback.answer("❌ Произошла ошибка при изменении статуса", show_alert=True)


@admin_router.callback_query(F.data.startswith("sure_canceled_order_"))
@admin_required
async def sure_canceled_order_(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    order_id = int(callback.data.split("_")[-1])
    admin_tg_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(admin_tg_id)
    admin_id = admin.admin_id
    main_message = await callback.message.edit_text(
        text="Напишите причину отмены заказа\n (Причина отмены будет видна пользователю)",
        reply_markup=await KbAdmin.need_reason_to_cancel(order_id),
    )
    await state.set_state(AdminReasonToCancellation.waiting_reason_to_cancellation)
    await state.update_data(
        order_id=order_id,
        main_message_id=main_message.message_id,
        admin_id=admin_id,
        chat_id=callback.message.chat.id,
    )


@admin_router.callback_query(F.data == "cancellation_order_by_admin_with_reason")
@admin_required
async def cancellation_order_by_admin_with_reason(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    admin_id = data.get("admin_id")
    order_id = data.get("order_id")
    reason = data.get("reason")
    status = await AdminQueries.get_order_status(order_id)
    try:
        if status == OrderStatus.CANCELLED or status == OrderStatus.COMPLETED:
            await callback.answer(
                text="Вы не можете отменить заказ, который уже был отменён или доставлен",
                show_alert=True,
            )
            return
        canceled = await AdminQueries.canceling_order_with_reason(
            order_id, admin_id, reason
        )
        if canceled:
            order_details = await AdminQueries.get_order_details(order_id)
            if not order_details:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return
            text = await admin_format_order_details(order_details)
            status = await AdminQueries.get_order_status(order_id)
            await callback.message.edit_text(
                text=text,
                reply_markup=await KbAdmin.kb_order_actions(
                    order_id, admin_permissions, status
                ),
                parse_mode="HTML",
            )
            await callback.answer(text="Заказ успешно отменён", show_alert=True)
            user_info = order_details.get("user", {})
            user_telegram_id = user_info.get("telegram_id")
            order_price = order_details.get("total_price")
            await OrderQueries.get_user_money_back(user_telegram_id, order_price)
            book_data = order_details.get("books")
            books = []
            for book in book_data:
                book_id = book.get("book_id")
                quantity = book.get("quantity")
                books.append((book_id, quantity))
            await BookQueries.add_books_back_when_canceled_order(books)
            if user_telegram_id:
                send_msg_to_user = await send_user_msg(
                    bot, order_id, user_telegram_id, status, reason
                )
                if not send_msg_to_user:
                    await callback.answer(
                        "⚠️ Статус изменен, но не удалось уведомить пользователя",
                        show_alert=True,
                    )
            else:
                print(
                    f"Не удалось получить telegram_id пользователя для заказа {order_id}"
                )
                await callback.answer(
                    "⚠️ Статус изменен, но не удалось найти пользователя для уведомления",
                    show_alert=True,
                )
            return
        await callback.answer(
            text="Произошла ошибка, попробуйте ещё раз", show_alert=True
        )
    except Exception as e:
        print(f"Error in admin_view_order: {e}")
        await callback.answer("❌ Ошибка при загрузке заказа", show_alert=True)


# admin_main_control_books
# admin_main_control_admins


# FMScontext hnd
@admin_router.message(AdminReasonToCancellation.waiting_reason_to_cancellation, F.text)
@admin_required
async def reason_to_cancellation(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    admin_id = data.get("admin_id")
    order_id = data.get("order_id")
    reason = message.text.strip()
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    try:
        main_message = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text=f"✅ Заказ №{order_id} будет отменён.\n📝 Причина: {reason}",
            reply_markup=await KbAdmin.cancel_order_by_admin_with_reason(order_id),
        )
        await state.update_data(
            main_message_id=main_message.message_id,
            order_id=order_id,
            reason=reason,
            admin_id=admin_id,
        )
    except Exception as e:
        print(f"Ошибка при обработке отмены заказа: {e}")


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
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
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
    all_old_messages = old_messages_to_delete.copy()
    if old_main_message_id:
        all_old_messages.append(old_main_message_id)
    for msg_id in all_old_messages:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")
    updated_appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
    status = await SupportQueries.check_appeal_status(appeal_id)
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
        reply_markup=await KbAdmin.support_appeal_actions_keyboard(appeal_id, status),
        parse_mode="Markdown",
    )
    hint_message = await message.answer("✅ Ваше сообщение отправлено пользователю")
    await state.update_data(
        last_hint_id=hint_message.message_id,
        messages_to_delete=new_messages_to_delete,
        main_message_id=main_message.message_id,
    )
    await asyncio.sleep(1)
    await hint_message.delete()


@admin_router.message(AdminSupportState.sending_appeal_id_for_find, F.text)
@admin_required
async def appeal_id_to_find(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    bot = message.bot
    data = await state.get_data()
    old_main_message_id = data.get("main_message_id")
    old_hint = data.get("last_hint_id", [])
    if old_hint:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=old_hint)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    try:
        appeal_id = int(message.text)
    except ValueError:
        hint_message = await message.answer(
            text="❌ Номер обращения должен быть числом. Попробуйте еще раз:"
        )
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    telegram_id = int(message.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    if not await AdminQueries.appeal_exists(appeal_id):
        hint_message = await message.answer(
            text=f"❌ Обращение с номером {appeal_id} не найдено."
        )
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    has_admin_permission = PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    )
    if has_admin_permission:
        can_open = True
    else:
        can_open = await AdminQueries.is_assigned_admin(appeal_id, admin.admin_id)
    if old_main_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=old_main_message_id
            )
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    if can_open:
        appeal = await AdminQueries.get_admin_appeal_by_id(appeal_id)
        if not appeal:
            error_message = await message.answer(
                text="❌ Обращение не найдено",
                reply_markup=await KbAdmin.go_back_to_find_filters(),
            )
            await state.update_data(
                messages_to_delete=[error_message.message_id],
                main_message_id=error_message.message_id,
            )
            return
        await AdminQueries.admin_visited(appeal_id)
        status = await SupportQueries.check_appeal_status(appeal_id)
        message_parts, main_text = await admin_appeal_split_messages(appeal, admin_name)
        messages_to_delete = []
        if not message_parts:
            main_message = await message.answer(
                text=main_text,
                reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                    appeal_id, status
                ),
                parse_mode="Markdown",
            )
            messages_to_delete.append(main_message.message_id)
        else:
            for i, part in enumerate(message_parts):
                part_text = part
                if len(message_parts) > 1:
                    part_text = (
                        f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
                    )
                msg = await message.answer(part_text, parse_mode="Markdown")
                messages_to_delete.append(msg.message_id)
            main_message = await message.answer(
                text=main_text,
                reply_markup=await KbAdmin.support_appeal_actions_keyboard(
                    appeal_id, status
                ),
                parse_mode="Markdown",
            )
            messages_to_delete.append(main_message.message_id)
        await state.update_data(
            messages_to_delete=messages_to_delete,
            main_message_id=main_message.message_id,
            appeal_id=appeal_id,
            current_step="in_appeal",
        )
    else:
        main_message = await message.answer(
            text=f"❌ У вас недостаточно прав для открытия обращения №{appeal_id}.\n\nНа него был назначен другой администратор",
            reply_markup=await KbAdmin.go_back_to_find_filters(),
        )
        await state.update_data(
            messages_to_delete=[],
            main_message_id=main_message.message_id,
        )


@admin_router.message(AdminSupportState.sending_username_for_find, F.text)
@admin_required
async def username_to_find(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    bot = message.bot
    data = await state.get_data()
    old_main_message_id = data.get("main_message_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception:
            pass
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    username = message.text.strip()
    if not username:
        hint_message = await message.answer(
            text="❌ Username не может быть пустым. Попробуйте еще раз:"
        )
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    if username.startswith("@"):
        username = username[1:]
    telegram_id = int(message.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(telegram_id)
    has_admin_permission = PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    )
    has_appeals = await AdminQueries.has_appeals_by_username(
        username=username,
        admin_id=admin.admin_id,
        has_admin_permission=has_admin_permission,
    )
    if not has_appeals:
        hint_message = await message.answer(
            text=f"❌ По username @{username} не найдено обращений."
        )
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    if old_main_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=old_main_message_id
            )
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    appeals_data, total_count = await AdminQueries.get_appeals_by_username(
        username=username,
        admin_id=admin.admin_id,
        has_admin_permission=has_admin_permission,
        page=0,
        items_per_page=10,
    )
    if not appeals_data:
        main_message = await message.answer(
            text=f"❌ По username @{username} не найдено обращений.",
            reply_markup=await KbAdmin.go_back_to_find_filters(),
        )
        await state.update_data(
            messages_to_delete=[],
            main_message_id=main_message.message_id,
        )
        return
    main_message = await message.answer(
        text=f"📋 Обращения пользователя @{username} (найдено: {total_count}):",
        reply_markup=await KbAdmin.universal_appeals_keyboard(
            appeals_data=appeals_data,
            page=0,
            total_count=total_count,
            callback_prefix="admin_open_appeal",
            page_callback="search_username_page",
            back_callback="support_my_closed",
            items_per_page=10,
        ),
    )
    await state.clear()
    await state.update_data(
        messages_to_delete=[],
        main_message_id=main_message.message_id,
        search_username=username,
        current_page=0,
        total_count=total_count,
    )
