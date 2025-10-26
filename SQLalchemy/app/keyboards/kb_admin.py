from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.admin_utils import PermissionChecker
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models import AdminPermission, AppealStatus

status_dict = {
    AppealStatus.IN_WORK: "🔧 В работе",
    AppealStatus.CLOSED_BY_ADMIN: "👤 Закрыт вами",
    AppealStatus.CLOSED_BY_USER: "👨‍🦱 Закрыт пользователем",
    AppealStatus.NEW: "🆕 Новое ",
}


class KbAdmin:
    @staticmethod
    async def admin_main_keyboard(admin_permissions: int) -> InlineKeyboardMarkup:
        keyboard = []
        if PermissionChecker.has_permission(
            admin_permissions, AdminPermission.VIEW_STATS
        ):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📊 Главная статистика", callback_data="admin_main_stats"
                    )
                ]
            )
        if PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_ORDERS
        ):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="🛒 Статистика заказов", callback_data="admin_main_orders"
                    )
                ]
            )
        if PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_BOOKS
        ):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📚 Управление книгами",
                        callback_data="admin_main_control_books",
                    )
                ]
            )
        if PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_ADMINS
        ):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="👥 Управление администраторами",
                        callback_data="admin_main_control_admins",
                    )
                ]
            )
        if PermissionChecker.has_permission(
            admin_permissions, AdminPermission.MANAGE_SUPPORT
        ):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📨 Поддержка", callback_data="admin_main_support"
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton(text="🔙 Выход", callback_data="main_menu")]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def admin_agreement() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Согласен с правилами общения",
                        callback_data="support_take_new",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_main_support"
                    )
                ],
            ]
        )

    @staticmethod
    async def support_main_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🆕 Взять новое обращение",
                        callback_data="agreement_before_new_appeal",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔧 Мои активные обращения",
                        callback_data="support_my_active",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📁 Мои закрытые обращения",
                        callback_data="support_my_closed",
                    )
                ],
                # [
                #     InlineKeyboardButton(
                #         text="📊 Обновить статистику", callback_data="support_my_stats"
                #     )
                # ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
            ]
        )

    @staticmethod
    async def kb_my_active_appeals(appeal_data) -> InlineKeyboardMarkup:
        keyboard = []
        for appeal in appeal_data:
            username = appeal.get("username") or ""
            admin_visit = appeal.get("admin_visit")
            appeal_id = appeal.get("appeal_id")
            if admin_visit:
                new_msg = ""
            else:
                new_msg = "💬 Новое сообщение"
            button_text = f"{username} {new_msg}"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text, callback_data=f"admin_open_appeal_{appeal_id}"
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main_support")]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def support_appeal_actions_keyboard(
        appeal_id: int, status: str = AppealStatus.IN_WORK
    ) -> InlineKeyboardMarkup:
        keyboard = []
        if status == AppealStatus.IN_WORK or status == AppealStatus.NEW:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="💬 Ответить пользователю",
                        callback_data=f"admin_support_reply_{appeal_id}",
                    )
                ],
            )
            keyboard.insert(
                1,
                [
                    InlineKeyboardButton(
                        text="🔒 Закрыть обращение",
                        callback_data=f"admin_appeal_close_{appeal_id}",
                    )
                ],
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад в поддержку", callback_data="admin_main_support"
                )
            ],
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def sure_close(appeal_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Не закрывать ",
                        callback_data=f"admin_open_appeal_{appeal_id}",
                    ),
                    InlineKeyboardButton(
                        text="✅ Закрыть",
                        callback_data=f"admin_appeal_sure_close_{appeal_id}",
                    ),
                ]
            ]
        )

    @staticmethod
    async def kb_closed_main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Все закрытые обращения",
                        callback_data="admin_last_appeals",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="#️⃣ Номер обращения",
                        callback_data="admin_closed_find_by_appeal_id",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="@ Username пользователя",
                        callback_data="admin_find_by_username",
                    )
                ],
                # [
                #     InlineKeyboardButton(
                #         text="📅 Дата обращения", callback_data="admin_find_by_date"
                #     )
                # ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в поддержку", callback_data="admin_main_support"
                    )
                ],
            ]
        )

    @staticmethod
    async def go_back_to_find_filters() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к фильтрам", callback_data="support_my_closed"
                    )
                ]
            ]
        )

    @staticmethod
    async def universal_appeals_keyboard(
        appeals_data: list,
        page: int = 0,
        total_count: int = 0,
        items_per_page: int = 10,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for appeal in appeals_data:
            appeal_id = appeal.get("appeal_id")
            username = appeal.get("username", "Без username")
            raw_status = appeal.get("status")
            status = status_dict.get(f"{raw_status}")
            date_field = appeal.get("created_date") or appeal.get("updated_at")
            date_str = date_field.strftime("%d.%m %H:%M")
            button_text = f"{status} | {username} | {date_str}"
            if len(button_text) > 30:
                available_chars = 30 - len(status) - len(date_str) - 6
            if available_chars > 3:
                short_username = (
                    username[:available_chars] + "..."
                    if len(username) > available_chars
                    else username
                )
                button_text = f"{status} | {short_username} | {date_str}"
            else:
                button_text = f"{status} | {date_str}"
            if len(button_text) > 30:
                button_text = button_text[:27] + "..."
            builder.button(
                text=button_text, callback_data=f"admin_open_appeal_{appeal_id}"
            )
        builder.adjust(1)
        if total_count > items_per_page:
            total_pages = (total_count + items_per_page - 1) // items_per_page
            pagination_buttons = []
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️",
                        callback_data=f"admin_all_closed_appeals_page_{page - 1}",
                    )
                )
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=f"{page + 1}/{total_pages}", callback_data="no_action"
                )
            )
            if page < total_pages - 1:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="➡️",
                        callback_data=f"admin_all_closed_appeals_page_{page + 1}",
                    )
                )
            builder.row(*pagination_buttons)
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="support_my_closed")
        )
        return builder.as_markup()
