from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class OrderProcessing:
    @staticmethod
    async def order_details(address_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
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
                        text="Адрес🏠", callback_data=f"change_address_{address_id}"
                    ),
                    InlineKeyboardButton(
                        text="Способ оплаты💳",
                        callback_data=f"change_payment_{address_id}",
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
        )

    @staticmethod
    async def kb_address_change(address_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗺️Город", callback_data=f"address_change_city_{address_id}"
                    ),
                    InlineKeyboardButton(
                        text="🛣️Улица",
                        callback_data=f"address_change_street_{address_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🏠Дом", callback_data=f"address_change_house_{address_id}"
                    ),
                    InlineKeyboardButton(
                        text="🚪Квартира",
                        callback_data=f"address_change_apartment_{address_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙Назад", callback_data=f"what_to_change_{address_id}"
                    )
                ],
            ]
        )

    @staticmethod
    async def kb_change_details(address_id) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Добавит или изменить данные",
                        callback_data=f"what_to_change_{address_id}",
                    )
                ],
                [InlineKeyboardButton(text="🔙Назад", callback_data="cart")],
            ]
        )

    @staticmethod
    async def kb_choose_address(addresses) -> InlineKeyboardMarkup:
        keyboard = []
        for address in addresses:
            if address["street"] is None or address["house"] is None:
                street = address.get("street", "")
                house = address.get("house", "")
                city = address.get("city", "")
                button_text = f"(Черновик){city} {street} {house}"
            else:
                button_text = f"{address['street']}, {address['house']}"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"address_{address['address_id']}",
                    )
                ]
            )
        (
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Добавит новый адрес", callback_data="new_address"
                    )
                ]
            ),
        )
        keyboard.append(
            [InlineKeyboardButton(text="🔙Назад", callback_data="cart")],
        )
        return InlineKeyboardMarkup()
