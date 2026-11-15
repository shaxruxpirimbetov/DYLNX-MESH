"""Ядро анонимного чата: доставка сообщений между гостем и владельцем стикера."""
import asyncio
import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message

from api import api
from db import db
from keyboards import guest_msg_kb, owner_msg_kb
from texts_old import t
from utils import short

log = logging.getLogger(__name__)

# Общий замок для «создать сообщение в API + запомнить его id» и для поллера,
# чтобы поллер не принял сообщение, только что созданное ботом, за новое.
relay_lock = asyncio.Lock()

CAPTIONABLE = {"photo", "video", "document", "audio", "voice", "animation"}
RELAYABLE = CAPTIONABLE | {"text", "location", "venue", "sticker", "video_note", "contact"}


def api_text(lang: str, msg: Message) -> str:
    """Что сохранить в бэкенд как текст сообщения."""
    if msg.text:
        return msg.text
    ct = msg.content_type
    label = {"photo": "media_photo", "video": "media_video", "voice": "media_voice",
             "location": "media_location", "venue": "media_location",
             "sticker": "media_sticker"}.get(ct, "media_other")
    tag = t(lang, label)
    if ct == "location" and msg.location:
        tag += f" https://maps.google.com/?q={msg.location.latitude},{msg.location.longitude}"
    return f"{tag} {msg.caption}" if msg.caption else tag


async def store(mesh_id: int, sender_tg: int, text: str):
    """Сохранить сообщение в бэкенд (история для админки). Ошибки не ломают чат."""
    try:
        async with relay_lock:
            created = await api.create_message(mesh_id, sender_tg, text)
            await db.mark_sent(created["id"])
    except Exception as err:
        log.warning("Failed to store message in API: %s", err)


async def deliver(bot: Bot, conv, sender_tg: int, *, text: str | None = None,
                  msg: Message | None = None, save: bool = True) -> str:
    """
    Отправить сообщение собеседнику по диалогу conv.
    Либо text (готовый текст), либо msg (оригинальное сообщение — копируем анонимно).
    Возвращает: ok | blocked | closed | unreachable | unsupported
    """
    if conv["status"] != "open":
        return "closed"
    to_owner = sender_tg == conv["guest_tg"]
    recipient = conv["owner_tg"] if to_owner else conv["guest_tg"]
    if to_owner and await db.is_blocked(conv["owner_tg"], sender_tg):
        return "blocked"

    r_lang = await db.get_lang(recipient)
    header = (t(r_lang, "hdr_to_owner", conv=conv["id"], short=short(conv["mesh_uuid"])) if to_owner
              else t(r_lang, "hdr_to_guest", conv=conv["id"]))
    kb = owner_msg_kb(r_lang, conv["id"]) if to_owner else guest_msg_kb(r_lang, conv["id"])

    sent_ids: list[int] = []
    try:
        if text is not None or (msg is not None and msg.text):
            body = text if text is not None else msg.text
            m = await bot.send_message(recipient, f"{header}\n\n{html.escape(body)}", reply_markup=kb)
            sent_ids.append(m.message_id)
        elif msg is not None and msg.content_type in CAPTIONABLE:
            cap = header + (f"\n\n{html.escape(msg.caption)}" if msg.caption else "")
            m = await bot.copy_message(recipient, msg.chat.id, msg.message_id, caption=cap[:1024],
                                       parse_mode="HTML", reply_markup=kb)
            sent_ids.append(m.message_id)
        elif msg is not None and msg.content_type in RELAYABLE:
            m1 = await bot.send_message(recipient, header, reply_markup=kb)
            m2 = await bot.copy_message(recipient, msg.chat.id, msg.message_id)
            sent_ids += [m1.message_id, m2.message_id]
        else:
            return "unsupported"
    except TelegramForbiddenError:
        return "unreachable"
    except TelegramBadRequest as err:
        log.warning("deliver failed: %s", err)
        return "unreachable"

    for mid in sent_ids:
        await db.map_msg(recipient, mid, conv["id"])
    if not await db.get_active_conv(recipient):
        await db.set_active_conv(recipient, conv["id"])
    await db.touch_conv(conv["id"])

    if save:
        s_lang = await db.get_lang(sender_tg)
        body = text if text is not None else api_text(s_lang, msg)
        asyncio.create_task(store(conv["mesh_id"], sender_tg, body))
    return "ok"
