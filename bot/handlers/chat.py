"""Анонимный чат: гость сканировал QR → пишет владельцу; владелец отвечает."""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton as IB, InlineKeyboardMarkup, Message,
                           ReactionTypeEmoji)

from api import api
from db import db
from keyboards import activate_kb, buy_kb, main_menu, quick_kb, unblock_kb
from relay import deliver
from texts import all_variants, t
from utils import RateLimiter, ago, is_expired

log = logging.getLogger(__name__)
router = Router(name="chat")
limiter = RateLimiter(1.2)


# ---------------------------------------------------------------- вход гостя
async def start_contact(message: Message, uuid: str, lang: str):
    """/start <uuid> — человек отсканировал QR и нажал «Написать владельцу»."""
    user_id = message.from_user.id
    try:
        mesh = await api.get_mesh(uuid)
    except Exception as err:
        log.exception("get_mesh failed: %s", err)
        return await message.answer(t(lang, "service_down"), reply_markup=main_menu(lang))

    if not mesh:
        return await message.answer(t(lang, "mesh_not_found"), reply_markup=main_menu(lang))
    if not mesh["is_active"] or not mesh.get("telegram_id"):
        return await message.answer(t(lang, "mesh_inactive"), reply_markup=activate_kb(lang, uuid))
    if is_expired(mesh):
        return await message.answer(t(lang, "mesh_expired"), reply_markup=buy_kb(lang) or main_menu(lang))

    owner_tg = int(mesh["telegram_id"])
    if owner_tg == user_id:
        return await message.answer(t(lang, "own_sticker"), reply_markup=main_menu(lang))
    if await db.is_blocked(owner_tg, user_id):
        return await message.answer(t(lang, "you_blocked"), reply_markup=main_menu(lang))

    conv, _ = await db.open_conv(mesh["id"], mesh["uuid"], owner_tg, user_id)
    await db.set_active_conv(user_id, conv["id"])
    await message.answer(t(lang, "contact_intro"), reply_markup=quick_kb(lang, conv["id"]))


async def _send_from_user(bot: Bot, message: Message | None, user_id: int, lang: str, conv,
                          *, text: str | None = None, reply_to: Message | None = None):
    """Общая отправка + понятные ответы пользователю."""
    first = conv["guest_tg"] == user_id and not await db.kv_get(f"delivered:{conv['id']}")
    result = await deliver(bot, conv, user_id, text=text, msg=message if text is None else None)
    target = reply_to or message
    if result == "ok":
        if first:
            await db.kv_set(f"delivered:{conv['id']}", "1")
            await target.answer(t(lang, "first_delivered"), reply_markup=main_menu(lang))
        elif message is not None:
            try:
                await message.react([ReactionTypeEmoji(emoji="👌")])
            except Exception:
                pass
    elif result == "blocked":
        await target.answer(t(lang, "you_blocked"))
    elif result == "closed":
        await target.answer(t(lang, "chat_closed"))
    elif result == "unsupported":
        await target.answer(t(lang, "unsupported"))
    else:
        await target.answer(t(lang, "service_down"))


# ---------------------------------------------------------------- быстрые причины
@router.callback_query(F.data.startswith("q:"))
async def quick_reason(cb: CallbackQuery, bot: Bot, lang: str):
    _, conv_id, key = cb.data.split(":")
    conv = await db.get_conv(int(conv_id))
    if not conv or conv["guest_tg"] != cb.from_user.id:
        return await cb.answer()
    if conv["status"] != "open":
        return await cb.answer(t(lang, "chat_closed"), show_alert=True)
    await db.set_active_conv(cb.from_user.id, conv["id"])
    if key == "custom":
        await cb.message.answer(t(lang, "write_custom"))
        return await cb.answer()
    if not limiter.hit(cb.from_user.id):
        return await cb.answer(t(lang, "slow_down"))
    # причину отправляем владельцу на ЕГО языке
    owner_lang = await db.get_lang(conv["owner_tg"])
    await _send_from_user(bot, None, cb.from_user.id, lang, conv,
                          text=t(owner_lang, f"q_{key}"), reply_to=cb.message)
    await cb.answer("✅")


# ---------------------------------------------------------------- кнопки под сообщениями
async def _conv_for(cb: CallbackQuery):
    conv = await db.get_conv(int(cb.data.split(":")[1]))
    if not conv or cb.from_user.id not in (conv["owner_tg"], conv["guest_tg"]):
        return None
    return conv


@router.callback_query(F.data.startswith("rep:"))
async def cb_reply(cb: CallbackQuery, lang: str):
    conv = await _conv_for(cb)
    if not conv:
        return await cb.answer()
    if conv["status"] != "open":
        return await cb.answer(t(lang, "chat_closed"), show_alert=True)
    await db.set_active_conv(cb.from_user.id, conv["id"])
    await cb.message.answer(t(lang, "reply_mode", conv=conv["id"]))
    await cb.answer()


@router.callback_query(F.data.startswith("omw:"))
async def cb_on_my_way(cb: CallbackQuery, bot: Bot, lang: str):
    conv = await _conv_for(cb)
    if not conv or conv["owner_tg"] != cb.from_user.id:
        return await cb.answer()
    if conv["status"] != "open":
        return await cb.answer(t(lang, "chat_closed"), show_alert=True)
    guest_lang = await db.get_lang(conv["guest_tg"])
    result = await deliver(bot, conv, cb.from_user.id, text=t(guest_lang, "omw_text"))
    await cb.answer(t(lang, "omw_done") if result == "ok" else t(lang, "service_down"), show_alert=result != "ok")


@router.callback_query(F.data.startswith("blk:"))
async def cb_block(cb: CallbackQuery, bot: Bot, lang: str):
    conv = await _conv_for(cb)
    if not conv or conv["owner_tg"] != cb.from_user.id:
        return await cb.answer()
    await db.block(conv["owner_tg"], conv["guest_tg"])
    await db.close_conv(conv["id"])
    await cb.message.answer(t(lang, "blocked_ok", conv=conv["id"]), reply_markup=unblock_kb(lang, conv["id"]))
    try:
        g_lang = await db.get_lang(conv["guest_tg"])
        await bot.send_message(conv["guest_tg"], t(g_lang, "chat_ended_other", conv=conv["id"]))
    except Exception:
        pass
    await cb.answer()


@router.callback_query(F.data.startswith("unb:"))
async def cb_unblock(cb: CallbackQuery, lang: str):
    conv = await _conv_for(cb)
    if not conv or conv["owner_tg"] != cb.from_user.id:
        return await cb.answer()
    await db.unblock(conv["owner_tg"], conv["guest_tg"])
    await cb.message.edit_text(t(lang, "unblocked_ok"))
    await cb.answer()


@router.callback_query(F.data.startswith("end:"))
async def cb_end(cb: CallbackQuery, bot: Bot, lang: str):
    conv = await _conv_for(cb)
    if not conv:
        return await cb.answer()
    if conv["status"] != "open":
        return await cb.answer(t(lang, "chat_closed"))
    await db.close_conv(conv["id"])
    await cb.message.answer(t(lang, "chat_ended_you", conv=conv["id"]), reply_markup=main_menu(lang))
    other = conv["guest_tg"] if cb.from_user.id == conv["owner_tg"] else conv["owner_tg"]
    try:
        o_lang = await db.get_lang(other)
        await bot.send_message(other, t(o_lang, "chat_ended_other", conv=conv["id"]))
    except Exception:
        pass
    await cb.answer()


@router.callback_query(F.data.startswith("sel:"))
async def cb_select(cb: CallbackQuery, lang: str):
    conv = await _conv_for(cb)
    if not conv or conv["status"] != "open":
        return await cb.answer(t(lang, "chat_closed"), show_alert=True)
    await db.set_active_conv(cb.from_user.id, conv["id"])
    await cb.message.answer(t(lang, "chat_selected", conv=conv["id"]))
    await cb.answer()


# ---------------------------------------------------------------- список чатов
def chats_kb(lang: str, user_id: int, convs) -> InlineKeyboardMarkup:
    rows = []
    for c in convs:
        key = "chat_row_owner" if c["owner_tg"] == user_id else "chat_row_guest"
        rows.append([
            IB(text=t(lang, key, conv=c["id"], ago=ago(c["last_at"], lang)), callback_data=f"sel:{c['id']}"),
            IB(text="✖️", callback_data=f"end:{c['id']}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("chats"))
@router.message(F.text.in_(all_variants("btn_chats")))
async def show_chats(message: Message, lang: str, state: FSMContext):
    await state.clear()
    convs = await db.open_convs_for(message.from_user.id)
    if not convs:
        return await message.answer(t(lang, "no_chat"), reply_markup=main_menu(lang))
    await message.answer(t(lang, "chats_title"), reply_markup=chats_kb(lang, message.from_user.id, convs))


# ---------------------------------------------------------------- любое сообщение = в чат
@router.message(StateFilter(None), ~F.text.startswith("/"))
async def relay_any(message: Message, bot: Bot, lang: str):
    user_id = message.from_user.id

    conv = None
    if message.reply_to_message:
        conv = await db.conv_by_msg(user_id, message.reply_to_message.message_id)
        if conv and conv["status"] != "open":
            return await message.answer(t(lang, "chat_closed"))
    if conv is None:
        conv = await db.get_active_conv(user_id)
    if conv is None:
        convs = await db.open_convs_for(user_id)
        if len(convs) == 1:
            conv = convs[0]
        elif len(convs) > 1:
            return await message.answer(t(lang, "pick_chat"), reply_markup=chats_kb(lang, user_id, convs))
        else:
            return await message.answer(t(lang, "no_chat"), reply_markup=main_menu(lang))

    if not limiter.hit(user_id):
        return await message.answer(t(lang, "slow_down"))
    await db.set_active_conv(user_id, conv["id"])
    await _send_from_user(bot, message, user_id, lang, conv)
