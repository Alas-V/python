from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class OrderProcessing:
    @staticmethod
    async def order_details(
        address_id, is_complete: bool = False
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Имя👤", callback_data=f"change_name_{address_id}"
                ),
                InlineKeyboardButton(
                    text="Номер телефона📞",
                    callback_data=f"change_phone_{address_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Город🗺️", callback_data=f"change_city_{address_id}"
                ),
                InlineKeyboardButton(
                    text="Улица🛣️",
                    callback_data=f"change_street_{address_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Дом🏠", callback_data=f"change_house_{address_id}"
                ),
                InlineKeyboardButton(
                    text="Квартира🚪",
                    callback_data=f"change_apartment_{address_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Комментарий💭",
                    callback_data=f"change_comment_{address_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙Назад", callback_data=f"edit_address_{address_id}"
                )
            ],
        ]
        if is_complete:
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        text="✅Выбрать этот адрес и продолжить",
                        callback_data=f"complete_address_{address_id}",
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_change_details(
        address_id, is_complete: bool = False
    ) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Добавит или изменить данные",
                    callback_data=f"what_to_change_{address_id}",
                )
            ],
            [
                InlineKeyboardButton(text="🔙Назад", callback_data="cart"),
                InlineKeyboardButton(
                    text="❌Удалить адрес", callback_data=f"delete_address_{address_id}"
                ),
            ],
        ]
        if is_complete:
            (
                keyboard.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            text="✅Выбрать этот адрес и продолжить",
                            callback_data=f"complete_address_{address_id}",
                        )
                    ],
                ),
            )
            keyboard.insert(
                2,
                [
                    InlineKeyboardButton(
                        text="💭 Комментарий к заказу",
                        callback_data=f"change_comment{address_id}",
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_choose_address(addresses) -> InlineKeyboardMarkup:
        keyboard = []
        max_addresses = 0
        for address in addresses:
            if max_addresses == 5:
                break
            city = address.get("city", "") or ""
            street = address.get("street", "") or ""
            house = address.get("house", "") or ""
            is_draft = not all([street, house])
            if is_draft:
                parts = [part for part in [city, street, house] if part]
                address_text = " ".join(parts) if parts else "Пустой адрес"
                button_text = f"📝 Черновик: {address_text}"
            else:
                parts = [part for part in [street, house, city] if part]
                button_text = f"🏠 {', '.join(parts)}"
            max_addresses += 1
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"edit_address_{address['address_id']}",
                    )
                ]
            )
        if max_addresses < 5:
            (
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text="➕ Добавит новый адрес", callback_data="new_address"
                        )
                    ]
                ),
            )
        keyboard.append(
            [InlineKeyboardButton(text="🔙Назад", callback_data="cart")],
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def kb_skip_state() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚪Нет номера квартиры",
                        callback_data="skip_state",
                    )
                ]
            ]
        )

    @staticmethod
    async def kb_delete_address(address_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌Удалить",
                        callback_data=f"sure_delete_address_{address_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Назад", callback_data=f"edit_address_{address_id}"
                    )
                ],
            ],
        )

    @staticmethod
    async def kb_after_delete() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить новый адрес", callback_data="new_address"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="choose_address")],
            ]
        )
