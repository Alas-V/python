from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import SupportState

support = Router()


@support.callback_query(F.data == "support")
async def contact_support(callback: CallbackQuery, state: FSMContext):
    pass
