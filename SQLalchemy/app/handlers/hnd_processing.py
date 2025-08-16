from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from utils.states import OrderForm
from aiogram.fsm.context import FSMContext
from keyboards.kb_order import Processing
from aiogram.types import CallbackQuery

processing = Router()


@processing.callback_query(F.data == "processing_cart")
async def start_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.name)
    data = await state.get_data()
    await callback.message.edit_text(
        await Processing.get_order_summary(data),
        reply_markup=await Processing.get_order_keyboard(data, "name"),
    )

    msg = await callback.message.answer("👤 Пожалуйста, введите ваше имя получателя:")
    await state.update_data(msg_id=msg.message_id)
    await callback.answer()
