from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class Processing:
    @staticmethod
    async def get_order_keyboard(
        data: dict, current_state: str
    ) -> InlineKeyboardMarkup:
        buttons = []
        fields = {
            "name": "👤 Имя",
            "email": "📧 Email",
            "phone": "📞Номер телефона",
            "city": "🏙️ Город",
            "street": "🛣️ Улица",
            "house": "🏠 Дом",
            "apartment": "🚪 Квартира",
            "delivery_date": "📅 Дата",
            "payment_method": "💳 Оплата",
            "comment": "📝 Комментарий",
        }
        for field, label in fields.items():
            if field == current_state:
                buttons.append(
                    InlineKeyboardButton(
                        text=f"➡️ {label} (заполняется)", callback_data=f"ignore"
                    )
                )
            elif field in data:
                buttons.append(
                    InlineKeyboardButton(
                        text=f"✏️ {label}: {data[field]}", callback_data=f"edit_{field}"
                    )
                )
            else:
                buttons.append(
                    InlineKeyboardButton(
                        text=f"◻️ {label} (не заполнено)", callback_data=f"edit_{field}"
                    )
                )
        keyboard = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        text="🔙Главное меню", callback_data="save_data_main_menu"
                    )
                ]
            ]
        )
        if len(data) == len(fields) - 1:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить заказ", callback_data="confirm_order"
                    )
                ]
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def get_order_summary(data: dict) -> str:
        text = "📝 Текущие данные заказа:\n\n"
        fields = [
            ("👤 Имя", "name"),
            ("📧 Email", "email"),
            (
                "🏙️ Адрес",
                lambda d: f"{d.get('city', '')}, {d.get('street', '')} {d.get('house', '')}"
                + (f", кв. {d['apartment']}" if "apartment" in d else ""),
            ),
            ("📅 Дата доставки", "delivery_date"),
            ("⏰ Время доставки", "delivery_time"),
            ("📝 Комментарий", "comment"),
            ("💳 Способ оплаты", "payment_method"),
        ]
        for label, field in fields:
            if isinstance(field, str):
                value = data.get(field, "не указано")
            else:
                value = field(data)
            text += f"{label}: {value}\n"
        return text
