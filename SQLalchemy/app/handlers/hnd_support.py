from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import SupportState
from queries.orm import SupportQueries
from keyboards.kb_support import SupportKeyboards
from text_templates import (
    appeal_hint_text,
    cooldown_text,
    text_appeal_split_messages,
    message_cooldown_text,
)
from aiogram.exceptions import TelegramBadRequest
import asyncio

support_router = Router()


async def delete_messages(bot, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            # await asyncio.sleep(0.1)
        except Exception as e:
            if "message to delete not found" not in str(
                e
            ) and "message can't be deleted" not in str(e):
                print(f"Ошибка удаления сообщения {message_id}: {e}")


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
    no_cooldown = await SupportQueries.can_create_appeal(telegram_id)
    if not no_cooldown:
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
    message_parts, main_text = await text_appeal_split_messages(appeal)
    main_message = await callback.message.edit_text(
        text=main_text,
        parse_mode="Markdown",
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status),
    )
    await callback.answer(text=hint_text, show_alert=True)
    hint_message = await callback.message.answer(
        text="💌 Опишите ваш вопрос или проблему в сообщении ниже\nМы ответим в ближайшее время!"
    )
    await state.set_state(SupportState.message_to_support)
    await state.update_data(
        appeal_id=appeal_id,
        main_message_id=main_message.message_id,
        last_hint_id=hint_message.message_id,
        user_messages=[],
        current_step="message_to_support",
    )


@support_router.callback_query(F.data.startswith("open_appeal_"))
async def open_appeal(callback: CallbackQuery, state: FSMContext):
    appeal_id = int(callback.data.split("_")[2])
    status = await SupportQueries.check_appeal_status(appeal_id)
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    if not appeal:
        await callback.answer("❌ Обращение не найдено", show_alert=True)
        return
    message_parts, main_text = await text_appeal_split_messages(appeal)
    messages_to_delete = []
    await callback.message.delete()
    if message_parts:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await callback.message.answer(part_text, parse_mode="Markdown")
            messages_to_delete.append(msg.message_id)
    main_message = await callback.message.answer(
        text=main_text,
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status),
        parse_mode="Markdown",
    )
    has_user_msg = await SupportQueries.has_user_msg(appeal_id)
    if not has_user_msg:
        hint_message = await callback.message.answer(
            text="💌 Опишите ваш вопрос или проблему в сообщении ниже\nМы ответим в ближайшее время!"
        )
        messages_to_delete.append(hint_message.message_id)
        last_hint_id = hint_message.message_id
    else:
        last_hint_id = None
    await state.update_data(
        appeal_id=appeal_id,
        messages_to_delete=messages_to_delete,
        main_message_id=main_message.message_id,
        last_hint_id=last_hint_id,
    )
    await callback.answer()
    await state.set_state(SupportState.message_to_support)


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
    await SupportQueries.close_appeal(appeal_id, who_close="user")
    status = await SupportQueries.check_appeal_status(appeal_id)
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    message_parts, main_text = await text_appeal_split_messages(appeal)
    await callback.message.edit_text(
        text=main_text,
        parse_mode="Markdown",
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status),
    )
    await callback.answer("✅ Обращение закрыто")


@support_router.callback_query(F.data.startswith("new_message_to_support_"))
async def new_msg_to_support(callback: CallbackQuery, state: FSMContext):
    appeal_id = int(callback.data.split("_")[4])
    pass


# FMScontext hnd
@support_router.message(SupportState.message_to_support)
async def message_to_support(message: Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()
    telegram_id = int(message.from_user.id)
    appeal_id = data["appeal_id"]
    old_messages_to_delete = data.get("messages_to_delete", [])
    last_hint_id = data.get("last_hint_id")
    old_main_message_id = data.get("main_message_id")
    no_message_cooldown = await SupportQueries.message_cooldown(telegram_id)
    if not no_message_cooldown:
        if last_hint_id:
            try:
                await bot.delete_message(
                    chat_id=message.chat.id, message_id=last_hint_id
                )
            except Exception:
                pass
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=message.message_id
            )
        except Exception:
            pass
        cooldown_time = await SupportQueries.get_message_cooldown_seconds(telegram_id)
        text = await message_cooldown_text(cooldown_time)
        hint_message = await message.answer(text=text)
        await state.update_data(last_hint_id=hint_message.message_id)
        return
    if last_hint_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_hint_id)
        except Exception:
            pass
    await SupportQueries.new_user_message(
        telegram_id=telegram_id, appeal_id=appeal_id, message=message.text
    )
    all_messages_to_delete = old_messages_to_delete.copy()
    if old_main_message_id:
        all_messages_to_delete.append(old_main_message_id)
    await delete_messages(bot, message.chat.id, all_messages_to_delete)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        print(f"Не удалось удалить сообщение пользователя: {e}")
    appeal = await SupportQueries.get_appeal_full(appeal_id)
    status = await SupportQueries.check_appeal_status(appeal_id)
    message_parts, main_text = await text_appeal_split_messages(appeal)
    new_messages_to_delete = []
    if message_parts:
        for i, part in enumerate(message_parts):
            part_text = part
            if len(message_parts) > 1:
                part_text = f"*Часть {i + 1} из {len(message_parts)}*\n\n" + part_text
            msg = await message.answer(part_text, parse_mode="Markdown")
            new_messages_to_delete.append(msg.message_id)
    main_message = await message.answer(
        text=main_text,
        reply_markup=await SupportKeyboards.kb_in_appeal(appeal_id, status),
        parse_mode="Markdown",
    )
    confirmation = await message.answer("✅ Сообщение отправлено!")
    await asyncio.sleep(2)
    await confirmation.delete()
    await state.update_data(
        messages_to_delete=new_messages_to_delete,
        main_message_id=main_message.message_id,
        last_hint_id=None,
        user_messages=[],
    )
