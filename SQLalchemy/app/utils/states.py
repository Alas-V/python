from aiogram.fsm.state import StatesGroup, State


class OrderForm(StatesGroup):
    name = State()
    phone = State()
    city = State()
    street = State()
    house = State()
    apartment = State()
    delivery_date = State()
    payment = State()
    comment = State()
    editing_field = State()


class Review(StatesGroup):
    pass


class SupportState(StatesGroup):
    message_to_support = State()
