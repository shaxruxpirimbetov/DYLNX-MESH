"""Mesh - DYLNX — Telegram-бот. Запуск: python bot.py"""
import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, TelegramObject

from api import api
from config import config
from db import db
from handlers import activate, chat, common, meshes
from poller import run_poller


class LangMiddleware(BaseMiddleware):
    """Регистрирует пользователя и прокидывает в хендлеры его язык (`lang`)."""

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict) -> Any:
        user = data.get("event_from_user")
        data["lang"] = await db.ensure_user(user.id, user.language_code) if user else "ru"
        return await handler(event, data)


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.bot_token:
        raise SystemExit("BOT_TOKEN is not set (.env)")

    await db.connect()
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(LangMiddleware())
    dp.callback_query.outer_middleware(LangMiddleware())

    # порядок важен: чат (ловит всё подряд) — последним
    dp.include_routers(common.router, activate.router, meshes.router, chat.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Mesh - DYLNX"),
        BotCommand(command="my", description="🏷 Мои стикеры / Stikerlarim"),
        BotCommand(command="chats", description="💬 Чаты / Chatlar"),
        BotCommand(command="activate", description="➕ Активировать / Faollashtirish"),
        BotCommand(command="buy", description="🛒 Купить / Sotib olish"),
        BotCommand(command="help", description="ℹ️ Помощь / Yordam"),
        BotCommand(command="lang", description="🌐 Язык / Til"),
    ])

    poller = asyncio.create_task(run_poller(bot))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        poller.cancel()
        await api.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
