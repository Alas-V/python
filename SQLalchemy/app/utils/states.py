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


class AdminInitiatedAppeal(StatesGroup):
    waiting_for_first_message = State()


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


class AdminAddNewAdmin(StatesGroup):
    waiting_for_username = State()
    waiting_for_admin_name = State()


class AdminSearchAdminByUsername(StatesGroup):
    waiting_for_username = State()


class AdminAddNewBook(StatesGroup):
    waiting_for_author_name = State()
    waiting_for_book_title = State()
    waiting_for_book_genre = State()
    waiting_for_book_year = State()
    waiting_for_book_price = State()
    waiting_for_book_quantity = State()
    waiting_for_book_cover = State()
    editing_field = State()
    editing_cover = State()
    editing_author = State()


class AdminAddingNewAuthor(StatesGroup):
    waiting_for_author_country = State()


class AdminChangeAuthorInExistingBook(StatesGroup):
    waiting_for_author_name = State()
    waiting_for_author_country = State()
    waiting_completion = State()


class AdminSetSale(StatesGroup):
    waiting_for_sale_amount = State()
    confirm_sale = State()


class AdminSearchBook(StatesGroup):
    waiting_for_book_name_for_search = State()


class UserSearchBook(StatesGroup):
    waiting_for_book_name = State()
