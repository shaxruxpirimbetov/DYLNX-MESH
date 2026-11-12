"""/start (включая deep-link с QR), меню, язык, помощь, покупка, отмена, /stats."""
from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api import api
from config import config
from db import db
from handlers.activate import start_activation
from handlers.chat import start_contact
from keyboards import buy_kb, lang_kb, main_menu
from texts import all_variants, t
from utils import find_uuid

router = Router(name="common")


@router.message(StateFilter("*"), Command("cancel"))
@router.message(StateFilter("*"), F.text.in_(all_variants("btn_cancel")))
async def cancel(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(t(lang, "cancelled"), reply_markup=main_menu(lang))


@router.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandObject, state: FSMContext, lang: str):
    """
    t.me/<bot>?start=<uuid>     — гость (страница open_mesh.html)
    t.me/<bot>?start=a_<uuid>   — активация (страница unactive_qr.html)
    t.me/<bot>?start=buy        — купить
    """
    await state.clear()
    arg = (command.args or "").strip()
    if arg == "buy":
        return await message.answer(t(lang, "buy"), reply_markup=buy_kb(lang) or main_menu(lang))
    uuid = find_uuid(arg)
    if not uuid:
        return await message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))
    if arg.startswith("a_"):
        return await start_activation(message, state, lang, uuid)
    await start_contact(message, uuid, lang)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))


@router.message(Command("help"))
@router.message(F.text.in_(all_variants("btn_help")))
async def help_(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(t(lang, "help"), reply_markup=main_menu(lang))


@router.message(Command("buy"))
@router.message(F.text.in_(all_variants("btn_buy")))
async def buy(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(t(lang, "buy"), reply_markup=buy_kb(lang) or main_menu(lang))


@router.message(Command("lang"))
@router.message(F.text.in_(all_variants("btn_lang")))
async def choose_lang(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("ru", "lang_choose"), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery):
    lang = cb.data.split(":")[1]
    await db.set_lang(cb.from_user.id, lang)
    await cb.message.delete()
    await cb.message.answer(t(lang, "lang_set"), reply_markup=main_menu(lang))
    await cb.answer()


@router.message(Command("stats"), F.from_user.id.in_(config.admin_ids))
async def stats(message: Message):
    s = await api.stats()
    await message.answer(
        "<b>📊 Mesh - DYLNX</b>\n\n"
        f"Всего стикеров: <b>{s['total']}</b>\n"
        f"🟢 Активных: <b>{s['active']}</b>\n"
        f"⚪️ Не активированных: <b>{s['inactive']}</b>\n"
        f"🔴 Истёкших: <b>{s['expired']}</b>\n"
        f"⏰ Истекают за 7 дней: <b>{s['expiring_soon']}</b>\n"
        f"👤 Владельцев: <b>{s['owners']}</b>\n"
        f"💬 Сообщений: <b>{s['messages']}</b> (сегодня {s['messages_today']})"
    )
