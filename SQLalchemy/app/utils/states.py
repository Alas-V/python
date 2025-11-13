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


class BookDetailsState(StatesGroup):
    going_to_book = State()


class ReviewState(StatesGroup):
    rating = State()
    title = State()
    body = State()
    editing_field = State()


class SupportState(StatesGroup):
    message_to_support = State()


class AdminSupportState(StatesGroup):
    message_from_support = State()
    sending_appeal_id_for_find = State()
    sending_username_for_find = State()
    waiting_for_message = State()


class AdminOrderState(StatesGroup):
    waiting_order_id = State()
    waiting_username = State()


class AdminReasonToCancellation(StatesGroup):
    waiting_reason_to_cancellation = State()
    waiting_confirmation = State()


class EditAdminPermissions(StatesGroup):
    editing_permissions = State()
