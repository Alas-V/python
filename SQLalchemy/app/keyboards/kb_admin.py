from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.admin_utils import PermissionChecker
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models import AdminPermission, AppealStatus, OrderStatus
from datetime import datetime

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
    async def in_admin_statistic() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ]
        )

    @staticmethod
    async def kb_admin_main_order(admin_permissions: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🆕 Новые заказы", callback_data="admin_orders_new"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚚 Заказы в доставке", callback_data="admin_orders_delivering"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📫 Доставленные заказы",
                    callback_data="admin_orders_completed",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменные заказы", callback_data="admin_orders_canceled"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Поиск по номеру заказа",
                    callback_data="admin_find_orders_by_id",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Поиск по @username",
                    callback_data="admin_find_orders_by_username",
                )
            ],
        ]
        # if PermissionChecker.has_permission(
        #     admin_permissions, AdminPermission.VIEW_STATS
        # ):
        #     keyboard.append(
        #         [
        #             InlineKeyboardButton(
        #                 text="📊 Экспорт в CSV", callback_data="admin_orders_export_csv"
        #             )
        #         ]
        #     )
        keyboard.append(
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_admin_menage_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔎 Просмотр Администраторов",
                        callback_data="admin_see_admins",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Добавить администратора",
                        callback_data="admin_add_new_admin",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Удалить администратора",
                        callback_data="admin_delate_admin",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
            ]
        )

    @staticmethod
    async def choose_admin_lvl() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👑 Супер-админы", callback_data="show_admin_superadmin"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛡️ Администраторы", callback_data="show_admin_admin"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚡ Менеджеры", callback_data="show_admin_manager"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔧  Модераторы", callback_data="show_admin_moderator"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_main_control_admins"
                    )
                ],
            ]
        )

    @staticmethod
    async def in_admin_details(admin_id: int, admin_role: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Управления правами",
                        callback_data=f"changing_admin_rights_{admin_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить администратора",
                        callback_data=f"admin_deleting_admin_with_{admin_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=f"show_admin_{admin_role}",
                    )
                ],
            ]
        )

    @staticmethod
    async def sure_to_delete_admin(admin_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Удалить",
                        callback_data=f"admin_sure_delete_admin_{admin_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=f"admin_view_admin_{admin_id}",
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_order_actions(
        order_id: int, admin_permissions, status
    ) -> InlineKeyboardMarkup:
        keyboard = []
        if status == OrderStatus.PROCESSING:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="🚚 В доставку",
                        callback_data=f"admin_order_status_delivering_{order_id}",
                    )
                ]
            )
        if status == OrderStatus.DELIVERING:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="✅ Завершить",
                        callback_data=f"admin_order_status_completed_{order_id}",
                    )
                ]
            )
        if status != OrderStatus.CANCELLED or status != OrderStatus.COMPLETED:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📞 Связаться",
                        callback_data=f"admin_contact_user_{order_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"sure_canceled_order_{order_id}",
                    ),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📞 Связаться",
                        callback_data=f"admin_contact_user_{order_id}",
                    ),
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 В меню заказов",
                    callback_data="admin_main_orders",
                )
            ],
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def sure_to_change_status(order_id: int, status: str) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔙 Назад ",
                    callback_data=f"admin_view_order_{order_id}",
                )
            ],
        ]
        if status == OrderStatus.CANCELLED:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="✅ Изменить статус заказа",
                        callback_data=f"sure_canceled_order_{order_id}",
                    )
                ],
            )
        else:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="✅ Изменить статус заказа",
                        callback_data=f"sure_change_status_{order_id}_{status}",
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def cancel_order_by_admin_with_reason(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data=f"admin_view_order_{order_id}"
                    ),
                    InlineKeyboardButton(
                        text="✅ Отменит заказ",
                        callback_data="cancellation_order_by_admin_with_reason",
                    ),
                ],
            ]
        )

    @staticmethod
    async def need_reason_to_cancel(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data=f"admin_view_order_{order_id}"
                    )
                ]
            ]
        )

    @staticmethod
    async def kb_open_order_for_admin(order_id: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Открыть заказ",
                        callback_data=f"admin_view_order_{order_id}",
                    )
                ]
            ]
        )
        return keyboard

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
    async def sure_to_made_admin(
        telegram_id: int, username: str
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅Сделать @{username} администратором ",
                        callback_data=f"made_new_admin_{telegram_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад ", callback_data="admin_main_control_admins"
                    )
                ],
            ]
        )

    @staticmethod
    async def open_main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Открыть главное меню ",
                        callback_data="main_menu",
                    )
                ]
            ]
        )

    @staticmethod
    async def add_new_admin_go_back() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад ", callback_data="admin_main_control_admins"
                    )
                ]
            ]
        )

    @staticmethod
    async def try_again_make_admin() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад ", callback_data="admin_main_control_admins"
                    )
                ]
            ]
        )

    @staticmethod
    async def manage_books_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📗 Добавить книгу", callback_data="admin_add_book"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Книги по жанрам", callback_data="catalog"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 Поиск книги", callback_data="admin_search_book"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")],
            ]
        )

    @staticmethod
    async def edit_permissions_keyboard(
        current_permissions: int, temp_permissions: int = None
    ) -> InlineKeyboardMarkup:
        permissions_builder = InlineKeyboardBuilder()
        permissions_mask = (
            temp_permissions if temp_permissions is not None else current_permissions
        )
        permissions_list = [
            (AdminPermission.MANAGE_SUPPORT, "📞 Поддержка"),
            (AdminPermission.MANAGE_ORDERS, "📦 Заказы"),
            (AdminPermission.MANAGE_BOOKS, "📚 Книги"),
            (AdminPermission.VIEW_STATS, "📊 Статистика"),
            (AdminPermission.MANAGE_ADMINS, "👑 Админы"),
        ]
        for permission, description in permissions_list:
            has_perm = PermissionChecker.has_permission(permissions_mask, permission)
            icon = "✅" if has_perm else "❌"
            permissions_builder.button(
                text=f"{icon} {description}",
                callback_data=f"toggle_perm_{permission.value}",
            )
        permissions_builder.adjust(2)
        actions_builder = InlineKeyboardBuilder()
        if temp_permissions is not None and temp_permissions != current_permissions:
            actions_builder.button(
                text="✅ Применить изменения", callback_data="apply_permission_changes"
            )
        actions_builder.button(text="🔙 Назад", callback_data="cancel_permission_edit")
        actions_builder.adjust(1)
        permissions_builder.attach(actions_builder)
        return permissions_builder.as_markup()

    @staticmethod
    async def kb_admin_find_orders(
        order_type: str,
        orders_data: list,
        page: int = 0,
        total_count: int = 0,
        items_per_page: int = 10,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for order in orders_data:
            order_id = order.get("order_id")
            price = order.get("price", 0)
            created_date = order.get("created_date")
            book_ids = order.get("book_id", [])
            username = order.get("username")
            first_name = order.get("user_first_name")
            items_count = len(book_ids) if book_ids else 0
            if isinstance(created_date, datetime):
                date_str = created_date.strftime("%d.%m %H:%M")
            else:
                date_str = "дата неизв."
            user_display = username or first_name or "Пользователь"
            if len(user_display) > 15:
                user_display = user_display[:15] + "..."
            button_text = f"#{order_id} | {items_count} поз. | {price}₽ | {date_str}"
            if len(button_text) > 40:
                button_text = button_text[:37] + "..."
            builder.button(
                text=button_text, callback_data=f"admin_view_order_{order_id}"
            )
        builder.adjust(1)
        if total_count > items_per_page:
            total_pages = (total_count + items_per_page - 1) // items_per_page
            pagination_buttons = []
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"page_admin_orders_{order_type}_{page - 1}",
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
                        text="Вперед ➡️",
                        callback_data=f"page_admin_orders_{order_type}_{page + 1}",
                    )
                )
            builder.row(*pagination_buttons)
        builder.row(
            InlineKeyboardButton(
                text="🔙Назад в меню заказов", callback_data="admin_main_orders"
            )
        )
        return builder.as_markup()

    # close on for find by username
    @staticmethod
    async def kb_admin_find_orders_by_username(
        orders_data: list,
        page: int = 0,
        total_count: int = 0,
        items_per_page: int = 10,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for order in orders_data:
            order_id = order.get("order_id")
            price = order.get("price", 0)
            created_date = order.get("created_date")
            book_ids = order.get("book_id", [])
            username = order.get("username")
            first_name = order.get("user_first_name")
            items_count = len(book_ids) if book_ids else 0
            if isinstance(created_date, datetime):
                date_str = created_date.strftime("%d.%m %H:%M")
            else:
                date_str = "дата неизв."
            user_display = username or first_name or "Пользователь"
            if len(user_display) > 15:
                user_display = user_display[:15] + "..."
            button_text = f"#{order_id} | {items_count} поз. | {price}₽ | {date_str}"
            if len(button_text) > 40:
                button_text = button_text[:37] + "..."
            builder.button(
                text=button_text, callback_data=f"admin_view_order_{order_id}"
            )
        builder.adjust(1)
        if total_count > items_per_page:
            total_pages = (total_count + items_per_page - 1) // items_per_page
            pagination_buttons = []
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"page_admin_find_by_username_orders_{username}_{page - 1}",
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
                        text="Вперед ➡️",
                        callback_data=f"page_admin_find_by_username_orders_{username}_{page + 1}",
                    )
                )
            builder.row(*pagination_buttons)
        builder.row(
            InlineKeyboardButton(
                text="🔙Назад в меню заказов", callback_data="admin_main_orders"
            )
        )
        return builder.as_markup()

    # one more for admin find
    @staticmethod
    async def kb_find_admins(
        admin_lvl: str,
        admin_data: list,
        page: int = 0,
        total_count: int = 0,
        items_per_page: int = 10,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for admin in admin_data:
            admin_id = admin.get("admin_id")
            admin_name = admin.name
            button_text = f"{admin_name}"
            if len(button_text) > 40:
                button_text = button_text[:37] + "..."
            builder.button(
                text=button_text, callback_data=f"admin_view_admin_{admin_id}"
            )
        builder.adjust(1)
        if total_count > items_per_page:
            total_pages = (total_count + items_per_page - 1) // items_per_page
            pagination_buttons = []
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"page_admin_see_admins_{admin_lvl}_{page - 1}",
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
                        text="Вперед ➡️",
                        callback_data=f"page_admin_see_admins_{admin_lvl}_{page + 1}",
                    )
                )
            builder.row(*pagination_buttons)
        builder.row(
            InlineKeyboardButton(text="🔙Назад", callback_data="admin_see_admins")
        )
        return builder.as_markup()

    @staticmethod
    async def get_back_to_order_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в меню заказов",
                        callback_data="admin_main_orders",
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
        callback_prefix: str = "admin_open_appeal",
        page_callback: str = "admin_all_closed_appeals_page_",
        back_callback: str = "support_my_closed",
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
                text=button_text, callback_data=f"{callback_prefix}_{appeal_id}"
            )
        builder.adjust(1)
        if total_count > items_per_page:
            total_pages = (total_count + items_per_page - 1) // items_per_page
            pagination_buttons = []
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️",
                        callback_data=f"{page_callback}_{page - 1}",
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
                        callback_data=f"{page_callback}_{page + 1}",
                    )
                )
            builder.row(*pagination_buttons)
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback))
        return builder.as_markup()
