from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from middleware.mw_admin import AdminMiddleware
from keyboards.kb_admin import KbAdmin
from keyboards.kb_user import UserKeyboards
from keyboards.kb_support import SupportKeyboards
from keyboards.kb_order import OrderProcessing
from queries.orm import (
    AdminQueries,
    SupportQueries,
    StatisticsQueries,
    BookQueries,
    OrderQueries,
    AuthorQueries,
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
    admin_list_text,
    admin_details,
    format_admin_permissions_text,
    get_book_text_for_admin,
    get_book_text_for_adding,
    get_book_details_on_sale,
    get_book_details,
    author_details_for_adding,
)
from utils.states import (
    AdminSupportState,
    AdminOrderState,
    AdminReasonToCancellation,
    EditAdminPermissions,
    AdminAddNewAdmin,
    AdminSearchAdminByUsername,
    AdminAddNewBook,
    AdminAddingNewAuthor,
    AdminChangeAuthorInExistingBook,
)
from models import AppealStatus, AdminPermission, OrderStatus, AdminRole
import asyncio
from aiogram.exceptions import TelegramBadRequest
from utils.admin_utils import PermissionChecker


admin_router = Router()
admin_router.callback_query.middleware(AdminMiddleware())
admin_router.message.middleware(AdminMiddleware())

GENRES = {
    "fantasy": "Фэнтази🚀",
    "horror": "Ужасы👻",
    "sciencefiction": "Научная Фантастика🌌",
    "detective": "Детектив🕵️",
    "classic": "Классическая литература🎭",
    "poetry": "Поэзия✒️",
}


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


def get_role_by_permissions(permissions: int) -> tuple[str, str]:
    """
    Определяет роль по весу наивысшего права
    """
    permission_weights = {
        AdminPermission.MANAGE_ADMINS: (AdminRole.SUPER_ADMIN, "superadmin"),
        AdminPermission.VIEW_STATS: (AdminRole.SUPER_ADMIN, "superadmin"),
        AdminPermission.MANAGE_BOOKS: (AdminRole.ADMIN, "admin"),
        AdminPermission.MANAGE_ORDERS: (AdminRole.MANAGER, "manager"),
        AdminPermission.MANAGE_SUPPORT: (AdminRole.MODERATOR, "moderator"),
    }
    highest_permission = AdminPermission.NONE
    for perm in [
        AdminPermission.MANAGE_ADMINS,
        AdminPermission.VIEW_STATS,
        AdminPermission.MANAGE_BOOKS,
        AdminPermission.MANAGE_ORDERS,
        AdminPermission.MANAGE_SUPPORT,
    ]:
        if permissions & perm:
            highest_permission = max(highest_permission, perm, key=lambda x: x.value)
    if highest_permission in permission_weights:
        return permission_weights[highest_permission]
    else:
        return AdminRole.NEW, "new"


async def send_admin_new_permission_notification(
    bot: Bot, user_telegram_id: int, new_permission
) -> bool:
    try:
        text = "Ваши права администратора были изменены: \n\n 🔑 Доступные права:\n"
        permissions_mask = (
            new_permission if new_permission is not None else "Нет новых прав"
        )
        permissions_list = [
            (AdminPermission.MANAGE_SUPPORT, "📞 Управление поддержкой"),
            (AdminPermission.MANAGE_ORDERS, "📦 Управление заказами"),
            (AdminPermission.MANAGE_BOOKS, "📚 Управление книгами"),
            (AdminPermission.VIEW_STATS, "📊 Просмотр статистики"),
            (AdminPermission.MANAGE_ADMINS, "👑 Управление администраторами"),
        ]
        for permission, description in permissions_list:
            if PermissionChecker.has_permission(permissions_mask, permission):
                text += f"├ {description} ✅\n"
        await bot.send_message(
            chat_id=user_telegram_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=await KbAdmin.open_main_menu(),
        )
        return True
    except Exception as e:
        print(f"Error in send_admin_new_permission_notification: {e}")
        return


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
        status_head = {
            OrderStatus.PROCESSING: "В обработке",
            OrderStatus.DELIVERING: "Передан в доставку",
            OrderStatus.COMPLETED: "Доставлен",
            OrderStatus.CANCELLED: "Отменён",
        }
        message_text = (
            f"📦 *Статус вашего заказа обновлён!*\n\n🆔 Номер заказа: *{order_id}*\n"
        )
        if status == OrderStatus.CANCELLED:
            message_text += (
                f"📊 Статус: *{status_head.get(status)}*\n\n"
                f"{status_messages.get(status, '')}\n{reason_to_cancellation}\n"
                f"💰 Деньги за заказ были возвращены на Ваш счет внутри бота"
                f"\n📨 При необходимости Вы можете обратиться в нашу службу поддержки"
            )
        elif status == OrderStatus.DELIVERING:
            message_text += (
                f"📊 Статус: *{status_head.get(status)}*\n\n"
                f"{status_messages.get(status, '')}\n\n"
                f"📱 Следить за статусом заказа можно в разделе «Мои заказы»"
            )
        elif status == OrderStatus.COMPLETED:
            message_text += (
                f"📊 Статус: *{status_head.get(status)}*\n\n"
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
    bot: Bot,
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
    data = await state.get_data()
    old_hint = data.get("last_hint_id", [])
    if old_hint:
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=old_hint
            )
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
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


@admin_router.callback_query(F.data.startswith("admin_find_orders_by_"))
@admin_required
async def admin_find_orders_by(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    by_what = str(callback.data.split("_")[-1])
    if by_what == "id":
        main_message = await callback.message.edit_text(
            text="Введите номер заказа для поиска",
            reply_markup=await KbAdmin.get_back_to_order_menu(),
        )
        await state.set_state(AdminOrderState.waiting_order_id)
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=callback.message.chat.id,
        )
        return
    main_message = await callback.message.edit_text(
        text="Введите username пользователя для поиска заказов",
        reply_markup=await KbAdmin.get_back_to_order_menu(),
    )
    await state.set_state(AdminOrderState.waiting_username)
    await state.update_data(
        main_message_id=main_message.message_id,
        chat_id=callback.message.chat.id,
    )
    return


@admin_router.callback_query(F.data.startswith("page_admin_find_by_username_orders_"))
@admin_required
async def page_admin_find_by_username_orders(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    try:
        page = int(callback.data.split("_")[-1])
        username = str(callback.data.split("_")[-2])
        telegram_id = await AdminQueries.get_telegram_id_by_username(username)
        total_count = await AdminQueries.get_admin_orders_count_telegram_id(telegram_id)
        orders_data = await AdminQueries.admin_get_user_orders_by_telegram_id_small(
            telegram_id, page=page
        )
        if not orders_data:
            await callback.answer("Больше заказов нет", show_alert=True)
            return
        await callback.message.edit_text(
            text=f"Все {total_count} заказы пользователя {username}",
            reply_markup=await KbAdmin.kb_admin_find_orders_by_username(
                orders_data=orders_data, page=page, total_count=total_count
            ),
        )
    except Exception as e:
        print(f"Error in admin_new_orders_pagination: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы", show_alert=True)


@admin_router.callback_query(F.data == "admin_main_control_admins")
@admin_required
async def admin_main_control_admins(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    data = await state.get_data()
    old_hint = data.get("last_hint_id", [])
    if old_hint:
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=old_hint
            )
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        admins_info = await AdminQueries.get_admins_info()
        admins_text = await admin_list_text(admins_info)
        await callback.message.edit_text(
            text=admins_text,
            reply_markup=await KbAdmin.kb_admin_menage_menu(),
            parse_mode="HTML",
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Error in admin_view_admins: {e}")
        await callback.answer("❌ Ошибка при загрузке ", show_alert=True)


@admin_router.callback_query(F.data == "admin_see_admins")
@admin_required
async def admin_see_admins(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    try:
        data = await state.get_data()
        old_hint = data.get("last_hint_id", [])
        if old_hint:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=old_hint
                )
            except Exception as e:
                print(f"Не удалось удалить старое сообщение: {e}")
        await callback.message.edit_text(
            text="Выберите уровень администратора для просмотра:",
            reply_markup=await KbAdmin.choose_admin_lvl(),
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Error in admin_view_admins: {e}")
        await callback.answer("❌ Ошибка при загрузке ", show_alert=True)


@admin_router.callback_query(F.data.startswith("show_admin_"))
@admin_required
async def show_admin(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    admin_lvl = str(callback.data.split("_")[-1])
    try:
        page = 0
        total_count = await AdminQueries.get_total_count_admins_by_lvl(admin_lvl)
        admin_data = await AdminQueries.get_admins_paginated(admin_lvl, page=page)
        if not admin_data:
            await callback.answer(
                text="❌ Администраторов данного уровня",
                show_alert=True,
            )
            return
        admin_text = {
            "superadmin": f" <b>👑 Управления администраторами уровня: Супер-Администратор</b>\n\nВсего администраторов данного уровня: {total_count}",
            "admin": f" <b>🛡️ Управления администраторами уровня: Администратор</b>\n\nВсего администраторов данного уровня: {total_count}",
            "manager": f" <b>⚡ Управления администраторами уровня: Менеджер</b>\n\nВсего администраторов данного уровня: {total_count}",
            "moderator": f" <b>🔧 Управления администраторами уровня: Модератор </b>\n\nВсего администраторов данного уровня: {total_count}",
        }
        await callback.message.edit_text(
            text=admin_text.get(admin_lvl),
            reply_markup=await KbAdmin.kb_find_admins(
                admin_lvl, admin_data, page=page, total_count=total_count
            ),
            parse_mode="HTML",
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in admin_new_orders: {e}")
        await callback.answer("❌ Ошибка при загрузке администраторов", show_alert=True)


@admin_router.callback_query(F.data.startswith("page_admin_see_admins_"))
@admin_required
async def page_admin_see_admins(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    try:
        page = int(callback.data.split("_")[-1])
        admin_lvl = str(callback.data.split("_")[-2])
        total_count = await AdminQueries.get_total_count_admins_by_lvl(admin_lvl)
        orders_data = await AdminQueries.get_admins_paginated(admin_lvl, page=page)
        if not orders_data:
            await callback.answer("Больше администраторов нет", show_alert=True)
            return
        admin_text = {
            "superadmin": f" <b>👑 Управления администраторами уровня: Супер-Администратор</b>\n\nВсего администраторов данного уровня: {total_count}",
            "admin": f" <b>🛡️ Управления администраторами уровня: Администратор</b>\n\nВсего администраторов данного уровня: {total_count}",
            "manager": f" <b>⚡ Управления администраторами уровня: Менеджер</b>\n\nВсего администраторов данного уровня: {total_count}",
            "moderator": f" <b>🔧 Управления администраторами уровня: Модератор </b>\n\nВсего администраторов данного уровня: {total_count}",
        }
        await callback.message.edit_text(
            text=admin_text.get(admin_lvl),
            reply_markup=await KbAdmin.kb_find_admins(
                admin_lvl, orders_data=orders_data, page=page, total_count=total_count
            ),
            parse_mode="HTML",
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in page_admin_see_admins_: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_view_admin_"))
@admin_required
async def admin_view_admin(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    try:
        admin_id = int(callback.data.split("_")[-1])
        admin = await AdminQueries.get_admin_by_id(admin_id)
        username = await AdminQueries.get_username_by_telegram_id(
            int(admin.telegram_id)
        )
        admin_detailed_text = await admin_details(admin, username)
        admin_role = await AdminQueries.get_admin_role_by_admin_id(admin_id)
        if not admin_role:
            await callback.answer(
                text="Произошла ошибка при открытие администратора", show_alert=True
            )
        rights = {
            AdminRole.SUPER_ADMIN: "superadmin",
            AdminRole.ADMIN: "admin",
            AdminRole.MANAGER: "manager",
            AdminRole.MODERATOR: "moderator",
        }
        main_message = await callback.message.edit_text(
            text=admin_detailed_text,
            reply_markup=await KbAdmin.in_admin_details(
                admin_id, admin_role=rights.get(admin_role, "Не найдена")
            ),
            parse_mode="HTML",
        )
        await state.update_data(
            main_message_id=main_message.message_id, current_admin_id=admin_id
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Error in admin_view_admin_: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_deleting_admin_with_"))
@admin_required
async def admin_deleting_admin_with(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    admin_id_to_delete = int(callback.data.split("_")[-1])
    admin = await AdminQueries.get_admin_by_id(admin_id_to_delete)
    admin_tg_id = int(callback.from_user.id)
    admin_who_delete = await AdminQueries.get_admin_by_telegram_id(admin_tg_id)
    if admin_who_delete.admin_id == admin_id_to_delete:
        await callback.answer(text="Вы не можете удалить себя", show_alert=True)
        return
    hint_message = await callback.message.answer(
        text=f"Вы уверены что хотите удалить администратора {admin.name}",
        reply_markup=await KbAdmin.sure_to_delete_admin(admin_id_to_delete),
    )
    await state.update_data(
        main_message_id=main_message_id,
        last_hint_id=hint_message.message_id,
        admin_id_to_delete=admin_id_to_delete,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_sure_delete_admin_"))
@admin_required
async def admin_sure_delete_admin(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception:
            pass
    admin_id_to_delete = int(callback.data.split("_")[-1])
    admin_role = await AdminQueries.get_admin_role_by_admin_id(admin_id_to_delete)
    rights = {
        AdminRole.SUPER_ADMIN: "superadmin",
        AdminRole.ADMIN: "admin",
        AdminRole.MANAGER: "manager",
        AdminRole.MODERATOR: "moderator",
    }
    admin_tg_id = int(callback.from_user.id)
    admin = await AdminQueries.get_admin_by_telegram_id(admin_tg_id)
    if admin.admin_id == admin_id_to_delete:
        await callback.answer(text="Вы не можете удалить себя", show_alert=True)
    deleted = await AdminQueries.delete_admin(admin_id_to_delete)
    if not deleted:
        await callback.answer("Не удалось удалить администратора", show_alert=True)
        return
    deleted_admin = await AdminQueries.get_admin_by_id(admin_id_to_delete)
    username = await AdminQueries.get_username_by_telegram_id(
        int(deleted_admin.telegram_id)
    )
    admin_detailed_text = await admin_details(deleted_admin, username)
    if main_message_id:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=main_message_id,
                text=admin_detailed_text,
                reply_markup=await KbAdmin.in_admin_details(
                    admin_id_to_delete, admin_role=rights.get(admin_role, "Не найдена")
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Не удалось отредактировать сообщение: {e}")
            await callback.message.answer(
                text=admin_detailed_text,
                reply_markup=await KbAdmin.in_admin_details(
                    admin_id_to_delete, admin_role=rights.get(admin_role, "Не найдена")
                ),
                parse_mode="HTML",
            )
    else:
        await callback.message.answer(
            text=admin_detailed_text,
            reply_markup=await KbAdmin.in_admin_details(
                admin_id_to_delete, admin_role=rights.get(admin_role, "Не найдена")
            ),
            parse_mode="HTML",
        )
    await state.clear()
    await callback.answer("Администратор был удален", show_alert=True)


@admin_router.callback_query(F.data.startswith("changing_admin_rights_"))
@admin_required
async def changing_admin_rights(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer(
            "❌ У вас нет прав для управления администраторами", show_alert=True
        )
        return
    try:
        admin_id = int(callback.data.split("_")[-1])
        admin_data = await AdminQueries.get_admin_by_id(admin_id)
        if not admin_data:
            await callback.answer("❌ Администратор не найден", show_alert=True)
            return
        await state.set_state(EditAdminPermissions.editing_permissions)
        await state.update_data(
            admin_id=admin_id,
            original_permissions=admin_data.permissions,
            temp_permissions=admin_data.permissions,
            original_message_id=callback.message.message_id,
            chat_id=callback.message.chat.id,
        )
        text = await format_admin_permissions_text(admin_data)
        await callback.answer()
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.edit_permissions_keyboard(
                admin_data.permissions
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in start_edit_permissions: {e}")
        await callback.answer("❌ Ошибка при начале редактирования", show_alert=True)


@admin_router.callback_query(F.data.startswith("toggle_perm_"))
@admin_required
async def toggle_permission(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    current_state = await state.get_state()
    if current_state != EditAdminPermissions.editing_permissions:
        await callback.answer("❌ Сессия редактирования завершена", show_alert=True)
        return
    try:
        data = await state.get_data()
        admin_id = data.get("admin_id")
        original_permissions = data.get("original_permissions")
        temp_permissions = data.get("temp_permissions", original_permissions)
        perm_value = int(callback.data.split("_")[-1])
        if PermissionChecker.has_permission(temp_permissions, perm_value):
            temp_permissions &= ~perm_value
        else:
            temp_permissions |= perm_value
        await state.update_data(temp_permissions=temp_permissions)
        admin_data = await AdminQueries.get_admin_by_id(admin_id)
        if not admin_data:
            await callback.answer("❌ Администратор не найден", show_alert=True)
            return
        text = await format_admin_permissions_text(admin_data, temp_permissions)
        await callback.answer()
        await callback.message.edit_text(
            text=text,
            reply_markup=await KbAdmin.edit_permissions_keyboard(
                original_permissions, temp_permissions
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Error in toggle_permission: {e}")
        await callback.answer("❌ Ошибка при изменении права", show_alert=True)


@admin_router.callback_query(F.data == "apply_permission_changes")
@admin_required
async def apply_permission_changes(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        data = await state.get_data()
        admin_id = data.get("admin_id")
        temp_permissions = data.get("temp_permissions")
        original_message_id = data.get("original_message_id")
        chat_id = data.get("chat_id")
        role_key, role_name = get_role_by_permissions(temp_permissions)
        success = await AdminQueries.update_admin_permissions_and_role(
            admin_id, temp_permissions, role_key
        )
        if success:
            admin_data = await AdminQueries.get_admin_by_id(admin_id)
            if not admin_data:
                await callback.answer(
                    "❌ Администратор не найден после обновления", show_alert=True
                )
                return
            username = await AdminQueries.get_username_by_telegram_id(
                admin_data.telegram_id
            )
            admin_detailed_text = await admin_details(admin_data, username)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=original_message_id,
                text=admin_detailed_text,
                reply_markup=await KbAdmin.in_admin_details(
                    admin_id,
                    admin_role=role_name,
                ),
                parse_mode="HTML",
            )
            await callback.answer("✅ Права обновлены!", show_alert=True)
            await send_admin_new_permission_notification(
                bot, admin_data.telegram_id, temp_permissions
            )
        else:
            await callback.answer("❌ Ошибка при обновлении прав", show_alert=True)
        await state.clear()
    except Exception as e:
        print(f"Error in apply_permission_changes: {e}")
        await callback.answer("❌ Ошибка при применении изменений", show_alert=True)
        await state.clear()


@admin_router.callback_query(F.data == "cancel_permission_edit")
@admin_required
async def cancel_permission_edit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    try:
        data = await state.get_data()
        admin_id = data.get("admin_id")
        original_message_id = data.get("original_message_id")
        chat_id = data.get("chat_id")
        admin_data = await AdminQueries.get_admin_by_id(admin_id)
        if admin_data:
            username = await AdminQueries.get_username_by_telegram_id(
                admin_data.telegram_id
            )
            admin_detailed_text = await admin_details(admin_data, username)
            admin_role = await AdminQueries.get_admin_role_by_admin_id(admin_id)
            rights = {
                AdminRole.SUPER_ADMIN: "superadmin",
                AdminRole.ADMIN: "admin",
                AdminRole.MANAGER: "manager",
                AdminRole.MODERATOR: "moderator",
            }
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=original_message_id,
                text=admin_detailed_text,
                reply_markup=await KbAdmin.in_admin_details(
                    admin_id, admin_role=rights.get(admin_role, "Не найдена")
                ),
                parse_mode="HTML",
            )
        await state.clear()
        await callback.answer("❌ Редактирование отменено", show_alert=True)
    except Exception as e:
        print(f"Error in cancel_permission_edit: {e}")
        await callback.answer("❌ Ошибка при отмене", show_alert=True)
        await state.clear()


@admin_router.callback_query(F.data == "admin_add_new_admin")
@admin_required
async def admin_add_new_admin(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        main_message = await callback.message.edit_text(
            text="Введите username пользователя, которого хотите сделать администратором",
            reply_markup=await KbAdmin.add_new_admin_go_back(),
        )
        await state.set_state(AdminAddNewAdmin.waiting_for_username)
        await state.update_data(
            main_message_id=main_message.message_id, chat_id=callback.message.chat.id
        )
        return
    except Exception as e:
        print(f"Error in admin_add_new_admin: {e}")
        await callback.answer(
            "❌ Ошибка при добавление администратора", show_alert=True
        )
        await state.clear()


@admin_router.callback_query(F.data.startswith("made_new_admin_"))
@admin_required
async def made_new_admin(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    telegram_id = int(callback.data.split("_")[-1])
    try:
        admin_id = await AdminQueries.made_new_admin_get_id(telegram_id)
        admin_data = await AdminQueries.get_admin_by_id(admin_id)
        text = await format_admin_permissions_text(admin_data)
        main_message = await callback.message.edit_text(text=text, parse_mode="HTML")
        hint_message = await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Введите имя Администратора \n\n <i>Имя будет видно пользователям</i>",
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewAdmin.waiting_for_admin_name)
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            admin_id=admin_id,
            chat_id=callback.message.chat.id,
        )
        await callback.answer(
            "Администратор был успешно создан\nНе забудьте установить имя администратору и назначить его права!",
            show_alert=True,
        )
    except Exception as e:
        print(f"Error in made_new_admin: {e}")
        await callback.answer("❌ Ошибка при создание администратора", show_alert=True)
        await state.clear()


@admin_router.callback_query(F.data == "admin_search_admin_by_username")
@admin_required
async def admin_search_admin_by_username(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_ADMINS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        main_message = await callback.message.edit_text(
            text="Введите @username администратора для поиска:",
            reply_markup=await KbAdmin.add_new_admin_go_back(),
        )
        await state.set_state(AdminSearchAdminByUsername.waiting_for_username)
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=callback.message.chat.id,
        )
        await callback.answer()
    except Exception as e:
        print(f"admin_search_admin_by_username: {e}")
        await callback.answer(
            "❌ Ошибка при попытке инициализации поиска администратора", show_alert=True
        )
        await state.clear()


@admin_router.callback_query(F.data == "admin_main_control_books")
@admin_required
async def admin_main_control_books(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        books_data = await BookQueries.get_books_for_admin()
        books_text_statistic = await get_book_text_for_admin(books_data)
        await callback.message.edit_text(
            text=books_text_statistic,
            reply_markup=await KbAdmin.manage_books_menu(),
            parse_mode="HTML",
        )
        await callback.answer()
    except Exception as e:
        print(f"admin_main_control_books: {e}")
        await callback.answer(
            "❌ Ошибка при открытие информации о книгах", show_alert=True
        )
        await state.clear()


@admin_router.callback_query(F.data == "admin_add_book")
@admin_required
async def admin_add_book(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        main_message = await callback.message.edit_text(
            text="Введите Автора Книги:\n\n<i>Если автор уже был добавлен ранее, то он откроется автоматически</i>",
            reply_markup=await KbAdmin.back_to_books_menu(),
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewBook.waiting_for_author_name)
        await state.update_data(
            main_message_id=main_message.message_id, chat_id=callback.message.chat.id
        )
        return
    except Exception as e:
        print(f"Ошибка admin_add_book: {e}")
        return


@admin_router.callback_query(F.data.startswith("admin_choose_author_for_new_book_"))
@admin_required
async def admin_choose_author_for_new_book(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    author_id = int(callback.data.split("_")[-1])
    try:
        book_id = await BookQueries.made_book_with_admin_id_get_book_id(author_id)
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        main_message = await callback.message.edit_text(
            text=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        hint_message = await bot.send_message(
            chat_id=callback.message.chat.id, text="Введите название книги:"
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_title)
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            chat_id=callback.message.chat.id,
            book_id=book_id,
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Ошибка admin_choose_author_for_new_book_: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
        return


@admin_router.callback_query(F.data.startswith("admin_skip_cover_add_"))
@admin_required
async def admin_skip_cover_add_(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    book_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(f"admin_skip_cover_add_ Не удалось удалить подсказку: {e}")
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id, column="book_photo_id", value=None
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка admin_skip_cover_add_: {e}")
        return


@admin_router.callback_query(F.data.startswith("admin_add_genre_to_new_book_"))
@admin_required
async def admin_add_genre_to_new_book_(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    book_id = int(callback.data.split("_")[-1])
    book_genre = callback.data.split("_")[-2]
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(f"admin_add_genre_to_new_book_ Не удалось удалить подсказку: {e}")
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id, column="book_genre", value=book_genre
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        hint_message = await bot.send_message(
            chat_id=chat_id, text="Напишите год издания книги: "
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_year)
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка admin_add_genre_to_new_book_: {e}")
        return


@admin_router.callback_query(F.data.startswith("admin_change_genre_to_new_book_"))
@admin_required
async def admin_change_genre_to_new_book(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    book_id = int(callback.data.split("_")[-1])
    book_genre = callback.data.split("_")[-2]
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(f"admin_change_genre_to_new_book_ Не удалось удалить подсказку: {e}")
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id, column="book_genre", value=book_genre
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        has_cover = await BookQueries.has_cover(book_id)
        if has_cover:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=main_message_id
                )
            except Exception as e:
                print(
                    f"admin_change_genre_to_new_book_ Не удалось удалить подсказку: {e}"
                )
            main_message = await bot.send_photo(
                chat_id=chat_id,
                photo=has_cover,
                caption=book_text,
                reply_markup=await KbAdmin.kb_new_book_changing(
                    book_id, book_done, new_book=True
                ),
                parse_mode="HTML",
            )
            await state.clear()
            await state.update_data(
                main_message_id=main_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
            return
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=book_text,
            reply_markup=await KbAdmin.kb_new_book_changing(
                book_id, book_done, new_book=True
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка admin_change_genre_to_new_book_: {e}")
        return


# opening book after publishing it to stock
# @admin_router.callback_query(F.data.startswith("admin_book_publishing_"))
# @admin_required
# async def admin_book_publishing(
#     callback: CallbackQuery,
#     bot: Bot,
#     state: FSMContext,
#     is_admin: bool,
#     admin_permissions: int,
#     admin_name: str,
# ):
#     if not PermissionChecker.has_permission(
#         admin_permissions, AdminPermission.MANAGE_BOOKS
#     ):
#         await callback.answer("❌ Недостаточно прав", show_alert=True)
#         return
#     try:
#         data = await state.get_data()
#         main_message_id = data.get("main_message_id")
#         book_id = int(callback.data.split("_")[-1])
#         last_hint_id = data.get("last_hint_id")
#         chat_id = data.get("chat_id") or callback.message.chat.id
#         if last_hint_id:
#             try:
#                 await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
#             except Exception as e:
#                 print(f"Не удалось удалить подсказку: {e}")
#         await AdminQueries.add_value_to_new_book(
#             book_id=book_id, column="book_in_stock", value=True
#         )
#         await callback.answer("✅ Книга была опубликована в продажу!", show_alert=True)
#         book_data = await BookQueries.get_book_info(book_id)
#         if not book_data:
#             await callback.answer("❌ Не удалось найти книгу", show_alert=True)
#             return
#         if book_data.get("book_on_sale"):
#             text = await get_book_details_on_sale(book_data)
#         else:
#             text = await get_book_details(book_data)
#         genre_in_text = GENRES.get(book_data["book_genre"], book_data["book_genre"])
#         book_cover = await BookQueries.has_cover(book_id)
#         can_manage_book_data = True
#         if book_cover:
#             try:
#                 if main_message_id:
#                     try:
#                         await bot.delete_message(
#                             chat_id=chat_id, message_id=main_message_id
#                         )
#                     except Exception:
#                         pass
#                 photo_message = await callback.message.answer_photo(
#                     photo=book_cover,
#                     caption=text,
#                     reply_markup=await UserKeyboards.book_details(
#                         book_data["book_id"],
#                         book_data["book_genre"],
#                         book_data["book_on_sale"],
#                         genre_in_text,
#                         can_manage_book_data,
#                     ),
#                     parse_mode="HTML",
#                 )
#                 await state.update_data(
#                     photo_message_id=photo_message.message_id,
#                     main_message_id=photo_message.message_id,
#                 )
#             except Exception as e:
#                 print(f"Ошибка при отправке фото: {e}")
#                 try:
#                     if main_message_id and chat_id:
#                         await bot.edit_message_text(
#                             chat_id=chat_id,
#                             message_id=main_message_id,
#                             text=text,
#                             reply_markup=await UserKeyboards.book_details(
#                                 book_data["book_id"],
#                                 book_data["book_genre"],
#                                 book_data["book_on_sale"],
#                                 genre_in_text,
#                                 can_manage_book_data,
#                             ),
#                             parse_mode="HTML",
#                         )
#                     else:
#                         await callback.message.answer(
#                             text,
#                             reply_markup=await UserKeyboards.book_details(
#                                 book_data["book_id"],
#                                 book_data["book_genre"],
#                                 book_data["book_on_sale"],
#                                 genre_in_text,
#                                 can_manage_book_data,
#                             ),
#                             parse_mode="HTML",
#                         )
#                 except Exception as e2:
#                     print(f"Ошибка при отправке текстовой версии: {e2}")
#                     await callback.message.answer(
#                         text,
#                         reply_markup=await UserKeyboards.book_details(
#                             book_data["book_id"],
#                             book_data["book_genre"],
#                             book_data["book_on_sale"],
#                             genre_in_text,
#                             can_manage_book_data,
#                         ),
#                         parse_mode="HTML",
#                     )
#         else:
#             try:
#                 if main_message_id and chat_id:
#                     await bot.edit_message_text(
#                         chat_id=chat_id,
#                         message_id=main_message_id,
#                         text=text,
#                         reply_markup=await UserKeyboards.book_details(
#                             book_data["book_id"],
#                             book_data["book_genre"],
#                             book_data["book_on_sale"],
#                             genre_in_text,
#                             can_manage_book_data,
#                         ),
#                         parse_mode="HTML",
#                     )
#                 else:
#                     await callback.message.answer(
#                         text,
#                         reply_markup=await UserKeyboards.book_details(
#                             book_data["book_id"],
#                             book_data["book_genre"],
#                             book_data["book_on_sale"],
#                             genre_in_text,
#                             can_manage_book_data,
#                         ),
#                         parse_mode="HTML",
#                     )
#             except Exception as e:
#                 print(f"Ошибка при отправке текстовой версии: {e}")
#                 await callback.message.answer(
#                     text,
#                     reply_markup=await UserKeyboards.book_details(
#                         book_data["book_id"],
#                         book_data["book_genre"],
#                         book_data["book_on_sale"],
#                         genre_in_text,
#                         can_manage_book_data,
#                     ),
#                     parse_mode="HTML",
#                 )
#     except Exception as e:
#         print(f"Ошибка admin_book_publishing: {e}")
#         import traceback

#         traceback.print_exc()


@admin_router.callback_query(F.data.startswith("admin_book_publishing_"))
@admin_required
async def admin_book_publishing(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        data = await state.get_data()
        main_message_id = data.get("main_message_id")
        book_id = int(callback.data.split("_")[-1])
        last_hint_id = data.get("last_hint_id")
        chat_id = data.get("chat_id") or callback.message.chat.id
        if last_hint_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
            except Exception as e:
                print(f"admin_book_publishing_ Не удалось удалить подсказку: {e}")
        more_than_zero = await BookQueries.more_than_zero_books(book_id)
        if more_than_zero:
            await AdminQueries.add_value_to_new_book(
                book_id=book_id, column="book_in_stock", value=True
            )
            await callback.answer(
                "✅ Книга была опубликована в продажу!", show_alert=True
            )
            has_cover = await BookQueries.has_cover(book_id)
            if has_cover:
                try:
                    await bot.delete_message(
                        chat_id=chat_id, message_id=main_message_id
                    )
                    main_message = await callback.message.answer(
                        text="Выберите следующее действие!",
                        reply_markup=await KbAdmin.kb_after_published_book(book_id),
                    )
                    await state.update_data(main_message_id=main_message.message_id)
                    return
                except Exception as e:
                    print(f"admin_book_publishing_  удалось удалить подсказку: {e}")
            main_message = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text="Выберите следующее действие!",
                reply_markup=await KbAdmin.kb_after_published_book(book_id),
            )
            await state.update_data(main_message_id=main_message.message_id)
        else:
            await callback.answer(
                "Вы не можете выставить книгу на продажу, количество экземпляров должно быть больше 0",
                show_alert=True,
            )
            return
    except Exception as e:
        print(f"Ошибка admin_book_publishing: {e}")


@admin_router.callback_query(F.data.startswith("cancel_admin_adding_book_"))
@admin_required
async def cancel_admin_adding_book(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    book_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    book_cover = await BookQueries.has_cover(book_id)
    if book_cover:
        try:
            if main_message_id:
                try:
                    await bot.delete_message(
                        chat_id=chat_id, message_id=main_message_id
                    )
                except Exception:
                    pass
            main_message = await callback.message.answer(
                text="Вы уверены что хотите выйти из добавления новой книги и удалить её ?",
                reply_markup=await KbAdmin.want_to_delete_new_book(book_id),
            )
            await callback.answer()
            await state.update_data(
                main_message_id=main_message.message_id, chat_id=chat_id
            )
            return
        except Exception as e:
            print(f"Ошибка cancel_admin_adding_book: {e}")
            return
    main_message = await callback.message.edit_text(
        text="Вы уверены что хотите выйти из добавления новой книги и удалить её ?",
        reply_markup=await KbAdmin.want_to_delete_new_book(book_id),
    )
    await callback.answer()
    await state.update_data(main_message_id=main_message.message_id, chat_id=chat_id)
    return


@admin_router.callback_query(F.data.startswith("delete_new_book_"))
@admin_required
async def delete_new_book(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    book_id = int(callback.data.split("_")[-1])
    try:
        deleted = await AdminQueries.delete_book(book_id)
        if deleted:
            await callback.answer("Книга была удалена")
        else:
            await callback.answer("Не удалось удалить книгу")
        books_data = await BookQueries.get_books_for_admin()
        books_text_statistic = await get_book_text_for_admin(books_data)
        await callback.message.edit_text(
            text=books_text_statistic,
            reply_markup=await KbAdmin.manage_books_menu(),
            parse_mode="HTML",
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"delete_new_book_: {e}")
        await callback.answer(
            "❌ Ошибка при открытие информации о книгах", show_alert=True
        )
        await state.clear()


@admin_router.callback_query(F.data.startswith("admin_change_book_"))
@admin_required
async def admin_change_book_(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    book_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    book_data = await BookQueries.get_book_info_for_new(book_id)
    book_text = await get_book_text_for_adding(book_data)
    book_done = await BookQueries.check_book_done(book_id)
    has_cover = await BookQueries.has_cover(book_id)
    if has_cover:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=main_message_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
        main_message = await bot.send_photo(
            chat_id=chat_id,
            photo=has_cover,
            caption=book_text + "\n\n<i>Выберите что вы хотите поменять в книге</i>",
            reply_markup=await KbAdmin.kb_new_book_changing(
                book_id, book_done, new_book=True
            ),
            parse_mode="HTML",
        )
        await state.update_data(main_message_id=main_message.message_id)
        return
    main_message = await bot.edit_message_text(
        message_id=main_message_id,
        chat_id=chat_id,
        text=book_text + "\n\n<i>Выберите что вы хотите отредактировать в книге</i>",
        reply_markup=await KbAdmin.kb_new_book_changing(
            book_id, book_done, new_book=True
        ),
        parse_mode="HTML",
    )
    await state.update_data(main_message_id=main_message.message_id)
    return


@admin_router.callback_query(F.data.startswith("admin_book_change_"))
@admin_required
async def admin_book_settings_(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    book_id = int(callback.data.split("_")[-1])
    what_to_change = str(callback.data.split("_")[-2])
    data = await state.get_data()
    last_hint_id = data.get("last_hint_id")
    main_message_id = data.get("main_message_id ")
    if last_hint_id:
        print(last_hint_id)
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception as e:
            print(f"admin_book_change_ Не удалось удалить подсказку: {e}")
    hint_dict = {
        "author": "👤 Введите Автора Книги:\n\n<i>Если автор уже был добавлен ранее, то он откроется автоматически</i>",
        "title": "📖 Укажите новое название книги:",
        "genre": "🔮 Выберите новый жанр книги: ",
        "year": "🗓 Укажите год издания книги ",
        "price": "💰 Укажите цену за 1шт. без учета скидки",
        "quantity": "📦 Укажите количество экземпляров книг для продажи ",
        "cover": "🖼 Отправьте обложку книги в формате фотографии",
    }
    if what_to_change == "genre":
        hint_message = await callback.message.answer(
            text=hint_dict.get(what_to_change),
            reply_markup=await KbAdmin.choose_genre_for_new_book_manually(book_id),
            parse_mode="HTML",
        )
    else:
        hint_message = await callback.message.answer(
            text=hint_dict.get(what_to_change), parse_mode="HTML"
        )
    if what_to_change == "cover":
        await state.set_state(AdminAddNewBook.editing_cover)
    # if what_to_change == "author":
    #     await state.set_state(AdminAddNewBook.editing_author)
    else:
        await state.set_state(AdminAddNewBook.editing_field)
    await state.update_data(
        last_hint_id=hint_message.message_id,
        what_to_change=what_to_change,
        chat_id=callback.message.chat.id,
        book_id=book_id,
        main_message_id=main_message_id,
    )
    await callback.answer()
    return


@admin_router.callback_query(
    F.data.startswith("admin_choose_author_for_choosing_book_")
)
@admin_required
async def admin_choose_author_for_choosing_book(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    author_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    book_id = data.get("book_id")
    if last_hint_id:
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=last_hint_id
            )
        except Exception as e:
            print(
                f"admin_choose_author_for_choosing_book_ Не удалось удалить подсказку: {e}"
            )
    try:
        await AdminQueries.assign_new_author_to_book(book_id, author_id)
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        has_cover = await BookQueries.has_cover(book_id)
        if has_cover:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=main_message_id
                )
            except Exception as e:
                print(
                    f"admin_choose_author_for_choosing_book_ Не удалось удалить подсказку: {e}"
                )
            main_message = await bot.send_photo(
                chat_id=chat_id,
                photo=has_cover,
                caption=book_text,
                reply_markup=await KbAdmin.kb_new_book_changing(
                    book_id, book_done, new_book=True
                ),
                parse_mode="HTML",
            )
            await state.clear()
            await state.update_data(
                main_message_id=main_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
            return
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=callback.message.chat.id,
            text=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=callback.message.chat.id,
            book_id=book_id,
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Ошибка admin_choose_author_for_choosing_book_: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
        return


@admin_router.callback_query(F.data == "admin_made_new_author")
@admin_required
async def admin_made_new_author(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        data = await state.get_data()
        author_name = data.get("author_name")
        author_id = await AuthorQueries.made_author_get_id(author_name)
        author_data = await AuthorQueries.get_author_data(author_id)
        author_complete = await AuthorQueries.check_author_completion(author_id)
        message_text = await author_details_for_adding(author_data)
        main_message = await callback.message.edit_text(
            text=message_text,
            reply_markup=await KbAdmin.adding_new_author(
                author_id=author_id, is_complete=author_complete
            ),
            parse_mode="HTML",
        )
        hint_message = await bot.send_message(
            chat_id=callback.message.chat.id, text="Введите страну автора:"
        )
        await state.set_state(AdminAddingNewAuthor.waiting_for_author_country)
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            author_id=author_id,
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"admin_made_new_author: {e}")


@admin_router.callback_query(F.data.startswith("delete_new_author_and_exit_"))
@admin_required
async def delete_new_author_and_exit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        author_id = int(callback.data.split("_")[-1])
        await AuthorQueries.delete_author(author_id)
        main_message = await callback.message.edit_text(
            text="Введите Автора Книги:\n\n<i>Если автор уже был добавлен ранее, то он откроется автоматически</i>",
            reply_markup=await KbAdmin.back_to_books_menu(),
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewBook.waiting_for_author_name)
        await state.update_data(
            main_message_id=main_message.message_id, chat_id=callback.message.chat.id
        )
        return
    except Exception as e:
        print(f"Error! delete_new_author_and_exit_ : {e}")
        return


@admin_router.callback_query(F.data.startswith("admin_change_author_"))
@admin_required
async def admin_change_author_(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        book_id = int(callback.data.split("_")[-1])
        old_author = await AuthorQueries.get_book_author_id(book_id)
        old_author = old_author if old_author else False
        main_message = await callback.message.edit_text(
            text="Введите Автора Книги:\n\n<i>Если автор уже был добавлен ранее, то он откроется автоматически</i>",
            reply_markup=await KbAdmin.kb_change_author(book_id),
            parse_mode="HTML",
        )
        await state.set_state(AdminChangeAuthorInExistingBook.waiting_for_author_name)
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=callback.message.chat.id,
            old_author_id=old_author,
            last_hint_id=False,
            book_id=book_id,
        )
        return
    except Exception as e:
        print(f"Error! admin_book_change_author: {e}")


@admin_router.callback_query(
    F.data.startswith("admin_made_new_author_for_choosing_book_")
)
@admin_required
async def admin_made_new_author_for_choosing_book(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        old_author_id = int(callback.data.split("_")[-1])
        new_author_name = str(callback.data.split("_")[-2])
        data = await state.get_data()
        book_id = data.get("book_id")
        new_author_id = await AuthorQueries.made_author_get_id(new_author_name)
        author_data = await AuthorQueries.get_author_data(new_author_id)
        author_complete = await AuthorQueries.check_author_completion(new_author_id)
        message_text = await author_details_for_adding(author_data)
        main_message = await callback.message.edit_text(
            text=message_text,
            reply_markup=await KbAdmin.changing_author_for_book(
                new_author_id=new_author_id,
                is_complete=author_complete,
                old_author_id=old_author_id,
            ),
            parse_mode="HTML",
        )
        hint_message = await bot.send_message(
            chat_id=callback.message.chat.id, text="Введите страну автора:"
        )
        await state.set_state(
            AdminChangeAuthorInExistingBook.waiting_for_author_country
        )
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            new_author_id=new_author_id,
            old_author_id=old_author_id,
            book_id=book_id,
            chat_id=callback.message.chat.id,
        )
        await callback.answer()
        return
    except Exception as e:
        print(f"Error! admin_made_new_author_for_choosing_book_  : {e}")


@admin_router.callback_query(
    F.data.startswith("delete_new_author_and_back_to_old_one_")
)
@admin_required
async def delete_new_author_and_back_to_old_one(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        new_author_id = int(callback.data.split("_")[-1])
        old_author_id = int(callback.data.split("_")[-2])
        data = await state.get_data()
        book_id = data.get("book_id")
        main_message_id = data.get("main_message_id")
        chat_id = data.get("chat_id")
        last_hint_id = data.get("last_hint_id")
        if last_hint_id:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=last_hint_id
                )
            except Exception as e:
                print(
                    f"delete_new_author_and_back_to_old_one_ Не удалось удалить подсказку: {e}"
                )
        await AuthorQueries.delete_author(new_author_id)
        try:
            book_data = await BookQueries.get_book_info_for_new(book_id)
            book_text = await get_book_text_for_adding(book_data)
            book_done = await BookQueries.check_book_done(book_id)
            has_cover = await BookQueries.has_cover(book_id)
            if has_cover:
                try:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id, message_id=main_message_id
                    )
                except Exception as e:
                    print(
                        f"Third layer error. delete_new_author_and_back_to_old_one:  {e}"
                    )
                main_message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=has_cover,
                    caption=book_text,
                    reply_markup=await KbAdmin.kb_new_book_changing(
                        book_id, book_done, new_book=True
                    ),
                    parse_mode="HTML",
                )
                await state.clear()
                await state.update_data(
                    main_message_id=main_message.message_id,
                    chat_id=chat_id,
                    book_id=book_id,
                )
                return
            main_message = await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text=book_text,
                reply_markup=await KbAdmin.kb_new_book_changing(
                    book_id, book_done, new_book=True
                ),
                parse_mode="HTML",
            )
            await state.clear()
            await state.update_data(
                main_message_id=main_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
            return
        except Exception as e:
            print(f"second layer Error!delete_new_author_and_back_to_old_one: {e}")
            return
    except Exception as e:
        print(f"Error!delete_new_author_and_back_to_old_one: {e} ")


@admin_router.callback_query(F.data.startswith("change_author_in_existing_book_"))
@admin_required
async def change_author_in_existing_book_(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    try:
        data = await state.get_data()
        book_id = data.get("book_id")
        main_message_id = data.get("main_message_id")
        chat_id = data.get("chat_id")
        new_author_id = int(callback.data.split("_")[-1])
        await AuthorQueries.assigned_new_author_to_book(new_author_id, book_id)
        try:
            book_data = await BookQueries.get_book_info_for_new(book_id)
            book_text = await get_book_text_for_adding(book_data)
            book_done = await BookQueries.check_book_done(book_id)
            has_cover = await BookQueries.has_cover(book_id)
            if has_cover:
                try:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id, message_id=main_message_id
                    )
                except Exception as e:
                    print(f"Third layer error. change_author_in_existing_book_:  {e}")
                main_message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=has_cover,
                    caption=book_text,
                    reply_markup=await KbAdmin.kb_new_book_changing(
                        book_id, book_done, new_book=True
                    ),
                    parse_mode="HTML",
                )
                await state.clear()
                await state.update_data(
                    main_message_id=main_message.message_id,
                    chat_id=chat_id,
                    book_id=book_id,
                )
                return
            main_message = await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text=book_text,
                reply_markup=await KbAdmin.kb_new_book_changing(
                    book_id, book_done, new_book=True
                ),
                parse_mode="HTML",
            )
            await state.clear()
            await state.update_data(
                main_message_id=main_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
            return
        except Exception as e:
            print(f"second layer Error!change_author_in_existing_book_: {e}")
            return
    except Exception as e:
        print(f"Error change_author_in_existing_book_: {e}")


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
            print(
                f"AdminSupportState.message_from_support Не удалось удалить подсказку: {e}"
            )
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
    if not username.startswith("@"):
        username = f"@{username}"
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


@admin_router.message(AdminOrderState.waiting_order_id, F.text)
@admin_required
async def waiting_order_id(
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
        order_id = int(message.text)
    except ValueError:
        hint_message = await message.answer(
            text="❌ Номер заказа должен быть числом. Попробуйте еще раз:"
        )
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    if order_id:
        order_data = await AdminQueries.get_order_details(order_id)
        if not order_data:
            hint_message = await message.answer("❌ Заказ не найден")
            await state.update_data(last_hint_id=hint_message.message_id)
            return
        text = await admin_format_order_details(order_data)
        try:
            status = await AdminQueries.get_order_status(order_id)
            main_message = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text=text,
                reply_markup=await KbAdmin.kb_order_actions(
                    order_id, admin_permissions, status
                ),
                parse_mode="HTML",
            )
            await state.update_data(
                main_message_id=main_message.message_id,
                order_id=order_id,
            )
        except Exception as e:
            print(f"Ошибка при открытие заказа (по ID): {e}")


@admin_router.message(AdminOrderState.waiting_username, F.text)
@admin_required
async def waiting_username(
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
    old_hint = data.get("last_hint_id", [])
    page = 0
    if old_hint:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=old_hint)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    username = str(message.text)
    if username:
        if username.startswith("@"):
            username = username[1:]
        user_telegram_id = await AdminQueries.get_telegram_id_by_username(username)
        total_count = await AdminQueries.get_admin_orders_count_telegram_id(
            user_telegram_id
        )
        if total_count < 1:
            hint_message = await message.answer(
                f"Не удалось найти заказы пользователя с username {username}"
            )
            await state.update_data(last_hint_id=hint_message.message_id)
            return
        orders_data = await AdminQueries.admin_get_user_orders_by_telegram_id_small(
            user_telegram_id
        )
        if not orders_data:
            hint_message = await message.answer("❌ Заказ не найден")
            await state.update_data(last_hint_id=hint_message.message_id)
            return
        main_message = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text=f"Все {total_count} заказы пользователя {username}",
            reply_markup=await KbAdmin.kb_admin_find_orders_by_username(
                orders_data=orders_data, page=page, total_count=total_count
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
        return


@admin_router.message(AdminAddNewAdmin.waiting_for_admin_name, F.text)
@admin_required
async def waiting_for_admin_name(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    if not PermissionChecker.has_permission(
        admin_permissions, AdminPermission.MANAGE_BOOKS
    ):
        await message.answer(
            "❌ У Вас недостаточно прав",
            reply_markup=await KbAdmin.try_again_make_admin(),
        )
        await state.clear()
        return
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    last_hint_id = data.get("last_hint_id")
    admin_id = data.get("admin_id")
    chat_id = data.get("chat_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    admin_name = message.text.strip().lower().capitalize()
    set_name_success = await AdminQueries.set_admin_new_name(admin_id, admin_name)
    if not set_name_success:
        last_hint = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text="Произошла ошибка, попробуйте написать имя администратора ещё раз",
        )
        await state.update_data(last_hint_id=last_hint.message_id)
        await state.set_state(AdminAddNewAdmin.waiting_for_admin_name)
        return
    admin_data = await AdminQueries.get_admin_by_id(admin_id)
    text = await format_admin_permissions_text(admin_data)
    await state.update_data(
        admin_id=admin_id,
        temp_permissions=admin_data.permissions,
        original_message_id=main_message_id,
        chat_id=chat_id,
    )
    await state.set_state(EditAdminPermissions.editing_permissions)
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=main_message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=await KbAdmin.edit_permissions_keyboard(admin_data.permissions),
    )
    return


@admin_router.message(AdminAddNewAdmin.waiting_for_username, F.text)
@admin_required
async def waiting_for_username(
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
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    username = message.text.strip()
    if not username.startswith("@"):
        username = f"@{username}"
    user = await AdminQueries.is_user_in_db(username)
    if not user:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text=f"❌ Пользователь @{username} не найден.\n\n"
                f"Для того чтобы сделать администратором пользователя: @{username}\n"
                f"<b>Он должен запускать бота</b> 📲 <i>(/start)</i>",
                reply_markup=await KbAdmin.try_again_make_admin(),
                parse_mode="HTML",
            )
            await state.clear()
            return
        except Exception as e:
            print(f"Ошибка при добавление нового администратора : {e}")
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text="❌ Произошла ошибка, попробуйте еще раз",
                reply_markup=await KbAdmin.try_again_make_admin(),
            )
            await state.clear()
            return
    is_user_admin = await AdminQueries.is_user_admin(user.telegram_id)
    if is_user_admin:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text=f"❌ Пользователь @{username} уже является администратором.\n\n",
                reply_markup=await KbAdmin.try_again_make_admin(),
                parse_mode="HTML",
            )
            await state.clear()
            return
        except Exception as e:
            print(
                f"Ошибка при добавление нового администратора, пользователь уже администратор: {e}"
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text="❌ Произошла ошибка, пользователь уже является администратором",
                reply_markup=await KbAdmin.try_again_make_admin(),
            )
            await state.clear()
            return
    try:
        if not PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_BOOKS
        ):
            await message.answer(
                "❌ У Вас недостаточно прав",
                reply_markup=await KbAdmin.try_again_make_admin(),
            )
            return
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text=f"Вы уверены что хотите сделать пользователя @{username} администратором? ",
            reply_markup=await KbAdmin.sure_to_made_admin(user.telegram_id, username),
        )
    except Exception as e:
        print(f"Ошибка при добавление нового администратора: {e}")
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text="❌ Произошла ошибка, попробуйте еще раз",
            reply_markup=await KbAdmin.try_again_make_admin(),
        )
        await state.clear()
        return


@admin_router.message(AdminSearchAdminByUsername.waiting_for_username, F.text)
@admin_required
async def AdminSearchAdminByUsername_waiting_for_username(
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
    if not username.startswith("@"):
        username = f"@{username}"
    try:
        admin = await AdminQueries.get_admin_by_username(username)
        admin_detailed_text = await admin_details(admin, username)
        admin_role = await AdminQueries.get_admin_role_by_admin_id(admin.admin_id)
        rights = {
            AdminRole.SUPER_ADMIN: "superadmin",
            AdminRole.ADMIN: "admin",
            AdminRole.MANAGER: "manager",
            AdminRole.MODERATOR: "moderator",
            AdminRole.NEW: "new",
            AdminRole.DELETED: "deleted",
        }
        main_message = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id,
            text=admin_detailed_text,
            reply_markup=await KbAdmin.in_admin_details(
                admin.admin_id, admin_role=rights.get(admin_role, "Не найдена")
            ),
            parse_mode="HTML",
        )
        await state.update_data(
            main_message_id=main_message.message_id, current_admin_id=admin.admin_id
        )
        return
    except Exception as e:
        print(f"admin_search_admin_by_username: {e}")
        print("❌ Ошибка AdminSearchAdminByUsername.waiting_for_username")


@admin_router.message(AdminAddNewBook.waiting_for_author_name, F.text)
@admin_required
async def AdminAddNewBook_waiting_for_author_name(
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
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    raw_author_name = message.text.strip()
    author = await AdminQueries.check_if_author_exist(raw_author_name)
    if author:
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=f"Выберите автора из предложенных по вашему запросу: {raw_author_name}.\n\n<i>Или создайте нового автора</i>",
            reply_markup=await KbAdmin.choose_author_for_new_book(
                author, raw_author_name
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            author_name=raw_author_name,
            main_message_id=main_message.message_id,
            chat_id=chat_id,
        )
        return
    main_message = await bot.edit_message_text(
        message_id=main_message_id,
        chat_id=chat_id,
        text=f"Не удалось найти автора по вашему запросу: {raw_author_name}.\n\n<i>Проверьте корректность ввода или создайте нового автора</i>",
        reply_markup=await KbAdmin.author_not_found_made_new(raw_author_name),
        parse_mode="HTML",
    )
    await state.clear()
    await state.update_data(
        author_name=raw_author_name,
        main_message_id=main_message.message_id,
        chat_id=chat_id,
    )


@admin_router.message(AdminAddNewBook.waiting_for_book_title, F.text)
@admin_required
async def AdminAddNewBook_waiting_for_book_title(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    book_title = message.text.strip()
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id,
            value=book_title,
            column="book_title",
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        hint_message = await bot.send_message(
            chat_id=chat_id,
            text="🔮 Выберите жанр книги: ",
            reply_markup=await KbAdmin.choose_genre_for_new_book(book_id),
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_genre)
        await state.update_data(
            main_message_id=main_message.message_id,
            last_hint_id=hint_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка AdminAddNewBook.waiting_for_book_title: {e}")
        return


@admin_router.message(AdminAddNewBook.waiting_for_book_year, F.text)
@admin_required
async def AdminAddNewBook_waiting_for_book_year(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    try:
        book_year = int(message.text.strip())
        try:
            await AdminQueries.add_value_to_new_book(
                book_id=book_id,
                value=book_year,
                column="book_year",
            )
            book_data = await BookQueries.get_book_info_for_new(book_id)
            book_text = await get_book_text_for_adding(book_data)
            book_done = await BookQueries.check_book_done(book_id)
            main_message = await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text=book_text,
                reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
                parse_mode="HTML",
            )
            hint_message = await bot.send_message(
                chat_id=chat_id,
                text="💰 Укажите стоимость книги (без учета скидки):",
            )
            await state.set_state(AdminAddNewBook.waiting_for_book_price)
            await state.update_data(
                main_message_id=main_message.message_id,
                last_hint_id=hint_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
        except Exception as e:
            print(f"Ошибка AdminAddNewBook.waiting_for_book_year: {e}")
    except Exception:
        hint_message = await bot.send_message(
            chat_id=chat_id,
            text="Ошибка, год издания книги числом\n\n<i>Например 1999</i>",
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_year)
        await state.update_data(last_hint_id=hint_message.message_id)


@admin_router.message(AdminAddNewBook.waiting_for_book_price, F.text)
@admin_required
async def AdminAddNewBook_waiting_for_book_price(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    try:
        book_price = int(message.text.strip())
        try:
            await AdminQueries.add_value_to_new_book(
                book_id=book_id,
                value=book_price,
                column="book_price",
            )
            book_data = await BookQueries.get_book_info_for_new(book_id)
            book_text = await get_book_text_for_adding(book_data)
            book_done = await BookQueries.check_book_done(book_id)
            main_message = await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text=book_text,
                reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
                parse_mode="HTML",
            )
            hint_message = await bot.send_message(
                chat_id=chat_id,
                text="📚 Укажите количество экземпляров книги для продажи: ",
            )
            await state.set_state(AdminAddNewBook.waiting_for_book_quantity)
            await state.update_data(
                main_message_id=main_message.message_id,
                last_hint_id=hint_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
        except Exception as e:
            print(f"Ошибка AdminAddNewBook.waiting_for_book_price: {e}")
    except Exception:
        hint_message = await bot.send_message(
            chat_id=chat_id,
            text="Ошибка, стоимость книги можно указать только числом\n\n<i>Например 2000</i>",
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_price)
        await state.update_data(last_hint_id=hint_message.message_id)


@admin_router.message(AdminAddNewBook.waiting_for_book_quantity, F.text)
@admin_required
async def AdminAddNewBook_waiting_for_book_quantity(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"Не удалось удалить старое сообщение: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    try:
        book_quantity = int(message.text.strip())
        try:
            await AdminQueries.add_value_to_new_book(
                book_id=book_id,
                value=book_quantity,
                column="book_quantity",
            )
            book_data = await BookQueries.get_book_info_for_new(book_id)
            book_text = await get_book_text_for_adding(book_data)
            book_done = await BookQueries.check_book_done(book_id)
            main_message = await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text=book_text,
                reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
                parse_mode="HTML",
            )
            hint_message = await bot.send_message(
                chat_id=chat_id,
                text="📷 Если есть обложка книги, отправьте фотографию и она будет добавлена. \n\n<i>Вы можете пропустить этот шаг и книга будет опубликована без обложки</i>",
                parse_mode="HTML",
                reply_markup=await KbAdmin.add_cover_or_skip(book_id),
            )
            await state.set_state(AdminAddNewBook.waiting_for_book_cover)
            await state.update_data(
                main_message_id=main_message.message_id,
                last_hint_id=hint_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
            )
        except Exception as e:
            print(f"Ошибка AdminAddNewBook.waiting_for_book_quantity: {e}")
    except Exception:
        hint_message = await bot.send_message(
            chat_id=chat_id,
            text="Ошибка, количество экземпляров книги можно указать только числом\n\n<i>Например 5</i>",
            parse_mode="HTML",
        )
        await state.set_state(AdminAddNewBook.waiting_for_book_quantity)
        await state.update_data(last_hint_id=hint_message.message_id)


@admin_router.message(AdminAddNewBook.waiting_for_book_cover, F.photo)
@admin_required
async def AdminAddNewBook_waiting_for_book_cover(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(
                f"AdminAddNewBook.waiting_for_book_cover Не удалось удалить подсказку: {e}"
            )
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение с фото: {e}")
    photo_photo_id = message.photo[-1].file_id
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id,
            value=photo_photo_id,
            column="book_photo_id",
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=main_message_id)
        except Exception:
            pass
        main_message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo_photo_id,
            caption=book_text,
            reply_markup=await KbAdmin.kb_add_new_book(book_id, book_done),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка AdminAddNewBook.waiting_for_book_cover: {e}")
        return


@admin_router.message(AdminAddNewBook.editing_field, F.text)
@admin_required
async def AdminAddNewBook_editing_field(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    what_to_change = data.get("what_to_change")
    db_column_dict = {
        "title": "book_title",
        "genre": "book_genre",
        "year": "book_year",
        "price": "book_price",
        "quantity": "book_quantity",
    }
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"AdminAddNewBook.editing_field Не удалось удалить подсказку: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение с фото: {e}")
    if (
        what_to_change == "year"
        or what_to_change == "price"
        or what_to_change == "quantity"
    ):
        try:
            number = int(message.text.strip())
            try:
                await AdminQueries.add_value_to_new_book(
                    book_id=book_id,
                    value=number,
                    column=db_column_dict.get(what_to_change),
                )
                book_data = await BookQueries.get_book_info_for_new(book_id)
                book_text = await get_book_text_for_adding(book_data)
                book_done = await BookQueries.check_book_done(book_id)
                has_cover = await BookQueries.has_cover(book_id)
                if has_cover:
                    try:
                        await bot.delete_message(
                            chat_id=message.chat.id, message_id=main_message_id
                        )
                    except Exception as e:
                        print(
                            f"AdminAddNewBook.editing_field Не удалось удалить подсказку: {e}"
                        )
                    main_message = await bot.send_photo(
                        chat_id=chat_id,
                        photo=has_cover,
                        caption=book_text,
                        reply_markup=await KbAdmin.kb_new_book_changing(
                            book_id, book_done, new_book=True
                        ),
                        parse_mode="HTML",
                    )
                    await state.clear()
                    await state.update_data(
                        main_message_id=main_message.message_id,
                        chat_id=chat_id,
                        book_id=book_id,
                        what_to_change=what_to_change,
                    )
                    return
                main_message = await bot.edit_message_text(
                    message_id=main_message_id,
                    chat_id=chat_id,
                    text=book_text,
                    reply_markup=await KbAdmin.kb_new_book_changing(
                        book_id, book_done, new_book=True
                    ),
                    parse_mode="HTML",
                )
                await state.clear()
                await state.update_data(
                    main_message_id=main_message.message_id,
                    chat_id=chat_id,
                    book_id=book_id,
                    what_to_change=what_to_change,
                )
                return
            except Exception as e:
                print(
                    f"Ошибка AdminAddNewBook.editing_field, F.text. number is a number: {e}"
                )
                return
        except ValueError:
            number_exception_dict = {
                "year": "год издания",
                "price": "стоимость",
                "quantity": "количество экземпляров",
            }
            exception_text = number_exception_dict.get(what_to_change)
            hint_message = await bot.send_message(
                chat_id=chat_id,
                text=f"Отправьте число для того чтобы изменить {exception_text}!",
            )
            await state.set_state(AdminAddNewBook.editing_field)
            await state.update_data(last_hint_id=hint_message.message_id)
            return
    raw_string = str(message.text.strip())
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id,
            value=raw_string,
            column=db_column_dict.get(what_to_change),
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        has_cover = await BookQueries.has_cover(book_id)
        if has_cover:
            try:
                await bot.delete_message(
                    chat_id=message.chat.id, message_id=main_message_id
                )
            except Exception as e:
                print(
                    f"AdminAddNewBook.editing_field Не удалось удалить подсказку: {e}"
                )
            main_message = await bot.send_photo(
                chat_id=chat_id,
                photo=has_cover,
                caption=book_text,
                reply_markup=await KbAdmin.kb_new_book_changing(
                    book_id, book_done, new_book=True
                ),
                parse_mode="HTML",
            )
            await state.clear()
            await state.update_data(
                main_message_id=main_message.message_id,
                chat_id=chat_id,
                book_id=book_id,
                what_to_change=what_to_change,
            )
            return
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=book_text,
            reply_markup=await KbAdmin.kb_new_book_changing(
                book_id, book_done, new_book=True
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
            what_to_change=what_to_change,
        )
    except Exception as e:
        print(f"Ошибка AdminAddNewBook.editing_field, F.text. raw_string  : {e}")
        return


@admin_router.message(AdminAddNewBook.editing_cover, F.photo)
@admin_required
async def AdminAddNewBook_editing_cover(
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
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(f"AdminAddNewBook.editing_cover Не удалось удалить подсказку: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение с фото: {e}")
    photo_photo_id = message.photo[-1].file_id
    try:
        await AdminQueries.add_value_to_new_book(
            book_id=book_id,
            value=photo_photo_id,
            column="book_photo_id",
        )
        book_data = await BookQueries.get_book_info_for_new(book_id)
        book_text = await get_book_text_for_adding(book_data)
        book_done = await BookQueries.check_book_done(book_id)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=main_message_id)
        except Exception:
            pass
        main_message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo_photo_id,
            caption=book_text,
            reply_markup=await KbAdmin.kb_new_book_changing(
                book_id, book_done, new_book=True
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
    except Exception as e:
        print(f"Ошибка AdminAddNewBook.editing_cover: {e}")
        return


@admin_router.message(AdminAddNewBook.editing_author, F.text)
@admin_required
async def AdminAddNewBook_editing_author(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    book_id = data.get("book_id")
    last_hint_id = data.get("last_hint_id")
    old_author_id = data.get("old_author_id")
    main_message_id = data.get("main_message_id")
    raw_author_name = message.text.strip()
    author = await AdminQueries.check_if_author_exist(raw_author_name)
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение : {e}")
    if author:
        hint_message = await bot.edit_message_text(
            message_id=last_hint_id,
            chat_id=chat_id,
            text=f"Выберите автора из предложенных по вашему запросу: {raw_author_name}.\n\n<i>Или создайте нового автора</i>",
            reply_markup=await KbAdmin.choose_author_for_changing_book(
                authors=author,
                raw_author_name=raw_author_name,
                book_id=book_id,
                old_author_id=old_author_id,
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            author_name=raw_author_name,
            last_hint_id=hint_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
            main_message_id=main_message_id,
        )
        return
    hint_message = await bot.edit_message_text(
        message_id=last_hint_id,
        chat_id=chat_id,
        text=f"Не удалось найти автора по вашему запросу: {raw_author_name}.\n\n<i>Проверьте корректность ввода или создайте нового автора</i>",
        reply_markup=await KbAdmin.author_not_found_made_new_for_changing_book(
            raw_author_name
        ),
        parse_mode="HTML",
    )
    await state.set_state(AdminAddNewBook.editing_author)
    await state.update_data(
        author_name=raw_author_name,
        last_hint_id=hint_message.message_id,
        chat_id=chat_id,
        book_id=book_id,
        main_message_id=main_message_id,
    )


@admin_router.message(AdminAddingNewAuthor.waiting_for_author_country, F.text)
@admin_required
async def AdminAddingNewAuthor_waiting_for_author_country(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    last_hint_id = data.get("last_hint_id")
    main_message_id = data.get("main_message_id")
    author_id = data.get("author_id")
    author_country = message.text.strip()
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception as e:
            print(
                f"AdminAddingNewAuthor.waiting_for_author_country Не удалось удалить подсказку: {e}"
            )
    try:
        await message.delete()
    except Exception as e:
        print(
            f"Не удалось удалить сообщение AdminAddingNewAuthor.waiting_for_author_country : {e}"
        )
    try:
        await AuthorQueries.add_data_to_column(
            author_id=author_id, value=author_country, column="author_country"
        )
        author_data = await AuthorQueries.get_author_data(author_id)
        author_complete = await AuthorQueries.check_author_completion(author_id)
        message_text = await author_details_for_adding(author_data)
        main_message = await bot.edit_message_text(
            text=message_text,
            chat_id=chat_id,
            message_id=main_message_id,
            parse_mode="HTML",
            reply_markup=await KbAdmin.adding_new_author(
                author_id=author_id, is_complete=author_complete
            ),
        )
        await state.clear()
        await state.update_data(
            main_message_id=main_message.message_id,
            author_id=author_id,
            chat_id=chat_id,
        )
        return
    except Exception as e:
        print(f"Ошибка AdminAddingNewAuthor.waiting_for_author_country: {e}")
        return


@admin_router.message(AdminChangeAuthorInExistingBook.waiting_for_author_name)
@admin_required
async def AdminChangeAuthorInExistingBook_waiting_for_author_name(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    main_message_id = data.get("main_message_id")
    old_author_id = data.get("old_author_id")
    book_id = data.get("book_id")
    new_author_name = message.text.strip()
    try:
        await message.delete()
    except Exception as e:
        print(
            f"Не удалось удалить сообщение AdminChangeAuthorInExistingBook.waiting_for_author_name : {e}"
        )
    author = await AdminQueries.check_if_author_exist(new_author_name)
    if author:
        main_message = await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text=f"Выберите автора из предложенных по вашему запросу: {new_author_name}.\n\n<i>Или создайте нового автора</i>",
            reply_markup=await KbAdmin.choose_author_for_changing_book(
                authors=author,
                raw_author_name=new_author_name,
                book_id=book_id,
                old_author_id=old_author_id,
            ),
            parse_mode="HTML",
        )
        await state.clear()
        await state.update_data(
            author_name=new_author_name,
            main_message_id=main_message.message_id,
            chat_id=chat_id,
            book_id=book_id,
        )
        return
    main_message = await bot.edit_message_text(
        message_id=main_message_id,
        chat_id=chat_id,
        text=f"Не удалось найти автора по вашему запросу: {new_author_name}.\n\n<i>Проверьте корректность ввода или создайте нового автора</i>",
        reply_markup=await KbAdmin.kb_made_new_author_for_existing_book(
            new_author_name, old_author_id, book_id
        ),
        parse_mode="HTML",
    )
    await state.clear()
    await state.update_data(
        new_author_name=new_author_name,
        old_author_id=old_author_id,
        main_message_id=main_message.message_id,
        chat_id=chat_id,
        book_id=book_id,
    )


@admin_router.message(AdminChangeAuthorInExistingBook.waiting_for_author_country)
# @admin_required
async def AdminChangeAuthorInExistingBook_waiting_for_author_country(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    admin_permissions: int,
    admin_name: str,
):
    data = await state.get_data()
    main_message_id = data.get("main_message_id")
    last_hint_id = data.get("last_hint_id")
    new_author_id = data.get("new_author_id")
    old_author_id = data.get("old_author_id")
    book_id = data.get("book_id")
    chat_id = data.get("chat_id")
    author_country = message.text.strip()
    try:
        await message.delete()
    except Exception as e:
        print(
            f"Не удалось удалить сообщение AdminAddingNewAuthor.waiting_for_author_country : {e}"
        )
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_hint_id)
        except Exception as e:
            print(
                f"AdminChangeAuthorInExistingBook_waiting_for_author_country Не удалось удалить подсказку: {e}"
            )
    try:
        await AuthorQueries.add_data_to_column(
            author_id=new_author_id, value=author_country, column="author_country"
        )
        print(f"{new_author_id}, {author_country} / 1")
        author_data = await AuthorQueries.get_author_data(new_author_id)
        print(f"{new_author_id}, {author_data} / 2")
        author_complete = await AuthorQueries.check_author_completion(new_author_id)
        print(f"{new_author_id}, {author_complete} / 3")
        message_text = await author_details_for_adding(author_data)
        print(f"{message_text} / 4")
        print(
            f"{chat_id},{main_message_id},{new_author_id},{old_author_id},{author_complete} / 5"
        )
        main_message = await bot.edit_message_text(
            text=message_text,
            chat_id=chat_id,
            message_id=main_message_id,
            parse_mode="HTML",
            reply_markup=await KbAdmin.changing_author_for_book(
                new_author_id=new_author_id,
                old_author_id=old_author_id,
                is_complete=author_complete,
            ),
        )
        await state.clear()
        # await state.set_state(AdminChangeAuthorInExistingBook.waiting_completion)
        # await state.update_data(
        #     main_message_id=main_message.message_id,
        #     new_author_id=new_author_id,
        #     old_author_id=old_author_id,
        #     book_id=book_id,
        #     chat_id=chat_id,
        # )
        # return
    except Exception as e:
        print(
            f"Ошибка AdminChangeAuthorInExistingBook_waiting_for_author_country: {type(e).__name__}: {e}"
        )
        import traceback

        traceback.print_exc()
        return
