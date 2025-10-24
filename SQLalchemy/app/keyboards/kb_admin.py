from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.admin_utils import PermissionChecker
from models import AdminPermission


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
                        text="🎯 Взять новое обращение",
                        callback_data="agreement_before_new_appeal",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Мои активные обращения",
                        callback_data="support_my_active",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📁 Мои закрытые обращения",
                        callback_data="support_my_closed",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Обновить статистику", callback_data="support_my_stats"
                    )
                ],
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
    async def support_appeal_actions_keyboard(appeal_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Ответить пользователю",
                        callback_data=f"admin_support_reply_{appeal_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔒 Закрыть обращение",
                        callback_data=f"support_close_{appeal_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в поддержку", callback_data="admin_main_support"
                    )
                ],
            ]
        )
