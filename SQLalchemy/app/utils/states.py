from aiogram.fsm.state import StatesGroup, State


class OrderForm(StatesGroup):
    name = State()
    email = State()
    phone = State()
    city = State()
    street = State()
    house = State()
    apartment = State()
    delivery_date = State()
    payment_method = State()
    comment = State()
