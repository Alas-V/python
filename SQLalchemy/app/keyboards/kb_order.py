from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class OrderProcessing:
    @staticmethod
    async def order_details() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Имя👤", callback_data="change_name"),
                    InlineKeyboardButton(
                        text="Номер телефона📞", callback_data="change_phone"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Адрес🏠", callback_data="change_address"
                    ),
                    InlineKeyboardButton(
                        text="Способ оплаты💳", callback_data="change_payment"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Комментарий💭", callback_data="change_comment"
                    )
                ],
                [InlineKeyboardButton(text="🔙Назад", callback_data="cart")],
            ]
        )

    @staticmethod
    async def kb_address_change() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗺️Город", callback_data="address_change_city"
                    ),
                    InlineKeyboardButton(
                        text="🛣️Улица", callback_data="address_change_street"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🏠Дом", callback_data="address_change_house"
                    ),
                    InlineKeyboardButton(
                        text="🚪Квартира", callback_data="address_change_apartment"
                    ),
                ],
                [InlineKeyboardButton(text="🔙Назад", callback_data="processing_cart")],
            ]
        )

    @staticmethod
    async def kb_change_details() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Добавит или изменить данные получателя",
                        callback_data="what_to_change",
                    )
                ],
                [InlineKeyboardButton(text="🔙Назад", callback_data="processing_cart")],
            ]
        )
