from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config import GIZMO_PHOTO_ID
from aiogram.fsm.context import FSMContext

from keyboards.main_menu import settings, inline_cars

from handlers.fsm.registration import Registration

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет !", reply_markup=settings())


@user_router.callback_query(F.data == "catalog")
async def catalog(callback: CallbackQuery):
    await callback.answer("Вы выбрали каталог")  # show_alert=True
    await callback.message.edit_text("Каталог", reply_markup=await inline_cars())


@user_router.message(Command("reg"))
async def reg_first(message: Message, state: FSMContext):
    await state.set_state(Registration.name)
    await message.answer("Введите Ваше имя")


@user_router.message(Registration.name)
async def reg_second(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.phone_number)
    await message.answer("Введите номер телефона")


@user_router.message(Registration.phone_number)
async def number_up(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    data = await state.get_data()
    await message.answer(f"Спасибо, {data['name']}, регистрация завершена.")
    await state.clear()


@user_router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.answer("Возврат в меню")
    await callback.message.edit_text("Меню", reply_markup=settings())


@user_router.message(F.text == "How are you?")
async def how_are_you(message: Message):
    await message.answer("Good !")


@user_router.message(F.photo)
async def get_photo(message: Message):
    await message.answer(f"Photo ID is - {message.photo[-1].file_id}")


@user_router.message(Command("show_photo"))
async def show_photo(message: Message):
    await message.answer_photo(
        photo=GIZMO_PHOTO_ID,
        caption="GIZMO!",
    )


@user_router.message(Command("my_id"))
async def my_id(message: Message):
    await message.answer(f"Ваш ID - {message.from_user.id}")


@user_router.message(Command("help"))
async def get_help(message: Message):
    await message.answer("This is /help")
