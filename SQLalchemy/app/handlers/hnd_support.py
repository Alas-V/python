from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import SupportState
from queries.orm import SupportQueries
from keyboards.kb_support import SupportKeyboards

support_router = Router()


@support_router.callback_query(F.data == "support")
async def contact_support(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.from_user.id)
    has_appeals = await SupportQueries.check_if_exist(telegram_id)
    if has_appeals:
        appeals = await SupportQueries.get_small_appeals_paginated(telegram_id, page=0)
        total_count = await SupportQueries.get_appeals_count(telegram_id)
        await callback.message.edit_text(
            text="🔀 Выберите одно из ваших обращений в поддержку или создайте новое",
            reply_markup=await SupportKeyboards.choose_appeal(
                appeals, page=0, total_count=total_count
            ),
        )
    else:
        await callback.message.edit_text(
            text="📨 Поддержка\n\nУ вас пока нет обращений. Создайте новое обращение:",
            reply_markup=await SupportKeyboards.support_main_menu(),
        )
