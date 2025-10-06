from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import SupportState
from queries.orm import SupportQueries
from keyboards.kb_support import SupportKeyboards
from text_templates import appeal_hint_text, cooldown_text, text_appeal_with_messages

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


@support_router.callback_query(F.data == "new_appeal")
async def new_appeal(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.from_user.id)
    cooldown = await SupportQueries.can_create_appeal(telegram_id)
    if not cooldown:
        cooldown_time = await SupportQueries.get_cooldown_minutes(telegram_id)
        last_appeal_id = await SupportQueries.get_last_appeal_id(telegram_id)
        text = await cooldown_text(cooldown_time)
        main_message = await callback.message.edit_text(
            text=text,
            reply_markup=await SupportKeyboards.kb_appeal_cooldown(last_appeal_id),
            parse_mode="Markdown",
        )
        return
    appeal_id = await SupportQueries.create_new_appeal(telegram_id)
    status = await SupportQueries.check_appeal_status(appeal_id)
    hint_text = await appeal_hint_text(appeal_id)
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    main_text, too_big = await text_appeal_with_messages(appeal)
    main_message = await callback.message.edit_text(
        text=main_text,
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status, too_big),
    )
    hint_message = await callback.message.answer(
        text=hint_text,
        parse_mode="Markdown",
    )
    await state.update_data(
        appeal_id=appeal_id,
        main_message_id=main_message.message_id,
        last_hint_id=hint_message.message_id,
        user_messages=[],
        current_step="message_to_support",
    )
    await state.set_state(SupportState.message_to_support)
    await callback.answer()


@support_router.callback_query(F.data.startswith("open_appeal_"))
async def open_appeal(callback: CallbackQuery):
    appeal_id = int(callback.data.split("_")[2])
    status = await SupportQueries.check_appeal_status(appeal_id)
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    main_text, too_big = await text_appeal_with_messages(appeal)
    await callback.message.edit_text(
        text=main_text,
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status, too_big),
    )
    await callback.answer()


@support_router.callback_query(F.data.startswith("close_appeal_"))
async def close_appeal(callback: CallbackQuery):
    appeal_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        text="Вы уверены что хотите закрыть это обращение?\nСоздавать обращения можно только раз в 60 минут❗ \n\n(Закрытое ранее обращения нельзя открывать заново)",
        reply_markup=await SupportKeyboards.sure_close(appeal_id),
    )


@support_router.callback_query(F.data.startswith("appeal_sure_close_"))
async def appeal_sure_close(callback: CallbackQuery):
    appeal_id = int(callback.data.split("_")[3])
    await SupportQueries.close_appeal_by_user(appeal_id)
    status = await SupportQueries.check_appeal_status(appeal_id)
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    main_text, too_big = await text_appeal_with_messages(appeal)
    await callback.message.edit_text(
        text=main_text,
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status, too_big),
    )
    await callback.answer("✅ Обращение закрыто")


# @support_router.callback_query(F.data.startswith("all_messages_appeal_"))  #{appeal_id}
# @support_router.callback_query(F.data.startswith("new_message_appeal_"))  #{appeal_id}
