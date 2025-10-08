from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_status_emoji(status: str) -> str:
    status_emojis = {
        "created": "🆕",
        "in_work": "🔧",
        "closed_by_user": "✅",
        "closed_by_admin": "✅",
    }
    return status_emojis.get(status, "📄")


class SupportKeyboards:
    @staticmethod
    async def choose_appeal(
        appeals: list, page: int = 0, total_count: int = 0
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for appeal in appeals:
            appeal_id, created_date, status = appeal
            status_emoji = get_status_emoji(status)
            button_text = f"📅 {created_date.strftime('%d.%m')} | {status_emoji}"
            builder.button(text=button_text, callback_data=f"open_appeal_{appeal_id}")
        if total_count > 5:
            pagination_buttons = []
            total_pages = (total_count + 4) // 5
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад", callback_data=f"appeals_page_{page - 1}"
                    )
                )
            if page < total_pages - 1:
                pagination_buttons.append(
                    InlineKeyboardButton(
                        text="Вперед ➡️", callback_data=f"appeals_page_{page + 1}"
                    )
                )
            if pagination_buttons:
                builder.row(*pagination_buttons)
            builder.row(
                InlineKeyboardButton(
                    text="📝 Создать новое обращение", callback_data="new_appeal"
                )
            )
            builder.row(
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            )
        return builder.as_markup()

    @staticmethod
    async def support_main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Создать обращение", callback_data="new_appeal")
        builder.button(text="🔙 Главное меню", callback_data="main_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def kb_in_appeal(appeal_id: id, status: str) -> InlineKeyboardMarkup:
        keyboard = []
        if status == "in_work":
            # keyboard.append(
            #     [
            #         InlineKeyboardButton(
            #             text="📝 Новое сообщение",
            #             callback_data=f"new_message_appeal_{appeal_id}",
            #         )
            #     ]
            # )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="❌ Закрыть обращение",
                        callback_data=f"close_appeal_{appeal_id}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        )

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_appeal_cooldown(last_appeal_id: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📝 Открыть прошлое обращение",
                    callback_data=f"open_appeal_{last_appeal_id}",
                )
            ],
            [InlineKeyboardButton(text="🔙 Главное Меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def sure_close(appeal_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Не закрывать ",
                        callback_data=f"open_appeal_{appeal_id}",
                    ),
                    InlineKeyboardButton(
                        text="✅ Закрыть",
                        callback_data=f"appeal_sure_close_{appeal_id}",
                    ),
                ]
            ]
        )
