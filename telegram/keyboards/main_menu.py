from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def greet_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог")],
            [KeyboardButton(text="Корзина"), KeyboardButton(text="Контакты")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню",
    )


def settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", callback_data="catalog")],
            [
                InlineKeyboardButton(text="Корзина", callback_data="cart"),
                InlineKeyboardButton(text="Контакты", callback_data="contacts"),
            ],
        ]
    )


cars = {
    "Mercedes": "https://www.mercedes.com",
    "BMW": "https://www.bmw.com",
    "Porsche": "https://www.porsche.com",
    "McLaren": "https://www.mclaren.com",
}


async def inline_cars():
    keyboard = InlineKeyboardBuilder()
    for car, website in cars.items():
        keyboard.add(InlineKeyboardButton(text=car, url=website))
    keyboard.row(InlineKeyboardButton(text="Меню", callback_data="main_menu"))
    return keyboard.adjust(2, 2, 1).as_markup()
