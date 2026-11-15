"""
Фоновый поллинг вместо WebSocket.

Сообщения между гостем и владельцем бот пересылает сразу сам (Telegram уже real-time).
Поллер раз в POLL_INTERVAL секунд проверяет API на НОВЫЕ сообщения, которые появились
не через этого бота — например, админ написал владельцу из админ-панели
(telegram_id = 0) или сообщение пришло из другого клиента — и доставляет их в Telegram.

Заодно: закрывает протухшие диалоги и раз в день напоминает об истечении стикеров.
"""
import asyncio
import html
import logging
from datetime import date, timedelta

from aiogram import Bot

from api import api
from config import config
from db import db
from relay import deliver, relay_lock
from texts import t
from utils import fmt_date, short

log = logging.getLogger(__name__)


async def _handle_external(bot: Bot, m: dict):
    owner = m.get("owner_telegram_id")
    if not owner:
        return
    owner_tg = int(owner)
    sender = int(m.get("telegram_id") or 0)

    if sender == 0:  # из админ-панели
        lang = await db.get_lang(owner_tg)
        text = f"{t(lang, 'hdr_admin', short=short(m['mesh_uuid']))}\n\n{html.escape(m['message'])}"
        try:
            await bot.send_message(owner_tg, text)
        except Exception as err:
            log.warning("admin message to %s failed: %s", owner_tg, err)
        return

    if sender == owner_tg:
        return  # владелец сам себе — нечего доставлять

    # пришло от гостя не через бота — заводим/продолжаем диалог и шлём владельцу
    await db.ensure_user(sender, None)
    if await db.is_blocked(owner_tg, sender):
        return
    conv, _ = await db.open_conv(m["mesh"], m["mesh_uuid"], owner_tg, sender)
    await deliver(bot, conv, sender, text=m["message"], save=False)


async def poll_messages(bot: Bot):
    last = await db.kv_get("last_message_id")
    if last is None:  # первый запуск: историю не рассылаем
        await db.kv_set("last_message_id", str(await api.last_message_id()))
        return
    last_id = int(last)
    async with relay_lock:
        new = await api.messages_after(last_id)
        external = []
        for m in new:
            last_id = max(last_id, m["id"])
            if not await db.pop_sent(m["id"]):
                external.append(m)
        await db.kv_set("last_message_id", str(last_id))
    for m in external:  # доставку делаем уже без замка
        await _handle_external(bot, m)


async def expiry_reminders(bot: Bot):
    today = date.today().isoformat()
    if await db.kv_get("expiry_day") == today:
        return
    await db.kv_set("expiry_day", today)
    until = (date.today() + timedelta(days=config.expiry_remind_days)).isoformat()
    for m in await api.meshes(status="active", until_lte=until):
        if not m.get("telegram_id"):
            continue
        tg = int(m["telegram_id"])
        try:
            await bot.send_message(tg, t(await db.get_lang(tg), "expiry_remind",
                                         short=short(m["uuid"]), until=fmt_date(m["until"])))
        except Exception:
            pass


async def run_poller(bot: Bot):
    log.info("Poller started (every %ss)", config.poll_interval)
    tick = 0
    last_err = None
    while True:
        try:
            await poll_messages(bot)
            if tick % 200 == 0:
                closed = await db.close_stale(config.chat_ttl_hours * 3600)
                if closed:
                    log.info("Closed %s stale chats", closed)
                await expiry_reminders(bot)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            # одну и ту же ошибку не спамим каждые 3 секунды
            if str(err) != last_err:
                log.warning("poller error: %s", err)
                last_err = str(err)
        else:
            if last_err:
                log.info("poller recovered")
                last_err = None
        tick += 1
        await asyncio.sleep(config.poll_interval)
