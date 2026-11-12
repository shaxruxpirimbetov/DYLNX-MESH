"""Активация купленного стикера: QR/ссылка/UUID → секретный код → номер (по желанию)."""
import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from db import db
from keyboards import cancel_kb, main_menu, phone_kb
from texts import MENU_TEXTS, all_variants, t
from utils import PHONE_RE, decode_qr, find_uuid, fmt_date, is_expired

log = logging.getLogger(__name__)
router = Router(name="activate")
MAX_ATTEMPTS = 5


class Act(StatesGroup):
    qr = State()
    password = State()
    phone = State()


async def _check_mesh(message: Message, state: FSMContext, uuid: str, lang: str) -> bool:
    """Проверить, что стикер можно активировать. True — можно, идём к паролю."""
    try:
        mesh = await api.get_mesh(uuid)
    except Exception as err:
        log.exception("get_mesh: %s", err)
        await message.answer(t(lang, "service_down"))
        return False
    user_id = message.chat.id
    if not mesh:
        await message.answer(t(lang, "act_bad_qr"))
        return False
    if mesh["is_active"] and mesh.get("telegram_id"):
        await state.clear()
        same = str(mesh["telegram_id"]) == str(user_id)
        await message.answer(t(lang, "act_already_mine" if same else "act_taken"), reply_markup=main_menu(lang))
        return False
    if is_expired(mesh):
        await state.clear()
        await message.answer(t(lang, "act_expired", until=fmt_date(mesh["until"])), reply_markup=main_menu(lang))
        return False
    await state.set_state(Act.password)
    await state.update_data(uuid=uuid)
    await message.answer(t(lang, "act_ask_pass"), reply_markup=cancel_kb(lang))
    return True


async def start_activation(message: Message, state: FSMContext, lang: str, uuid: str | None = None):
    await state.clear()
    if uuid:
        await _check_mesh(message, state, uuid, lang)
    else:
        await state.set_state(Act.qr)
        await message.answer(t(lang, "act_ask_qr"), reply_markup=cancel_kb(lang))


@router.message(Command("activate"))
@router.message(F.text.in_(all_variants("btn_activate")))
async def cmd_activate(message: Message, state: FSMContext, lang: str):
    await start_activation(message, state, lang)


@router.callback_query(F.data.startswith("act:"))
async def cb_activate(cb: CallbackQuery, state: FSMContext, lang: str):
    await cb.answer()
    await start_activation(cb.message, state, lang, cb.data.split(":", 1)[1])


@router.message(Act.qr, F.photo)
async def qr_photo(message: Message, state: FSMContext, bot: Bot, lang: str):
    buf = io.BytesIO()
    await bot.download(message.photo[-1], destination=buf)
    uuid = find_uuid(decode_qr(buf.getvalue()))
    if not uuid:
        return await message.answer(t(lang, "act_bad_qr"))
    await _check_mesh(message, state, uuid, lang)


@router.message(Act.qr, ~F.text.in_(MENU_TEXTS))
async def qr_text(message: Message, state: FSMContext, lang: str):
    uuid = find_uuid(message.text or message.caption)
    if not uuid:
        return await message.answer(t(lang, "act_bad_qr"))
    await _check_mesh(message, state, uuid, lang)


@router.message(Act.password, F.text, ~F.text.in_(MENU_TEXTS))
async def got_password(message: Message, state: FSMContext, lang: str):
    user_id = message.from_user.id
    if await db.attempts_recent(user_id) >= MAX_ATTEMPTS:
        await state.clear()
        return await message.answer(t(lang, "act_locked"), reply_markup=main_menu(lang))

    entered = message.text.strip()
    try:  # не оставляем секретный код в переписке
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    try:
        mesh = await api.get_mesh(data["uuid"])
    except Exception:
        return await message.answer(t(lang, "service_down"))
    if not mesh or entered != mesh.get("password"):
        await db.add_attempt(user_id)
        left = MAX_ATTEMPTS - await db.attempts_recent(user_id)
        if left <= 0:
            await state.clear()
            return await message.answer(t(lang, "act_locked"), reply_markup=main_menu(lang))
        return await message.answer(t(lang, "act_bad_pass", left=left))

    await state.update_data(password=entered)
    await state.set_state(Act.phone)
    await message.answer(t(lang, "act_ask_phone"), reply_markup=phone_kb(lang))


async def _finish(message: Message, state: FSMContext, lang: str, phone: str | None):
    data = await state.get_data()
    await state.clear()
    try:
        mesh = await api.activate(data["uuid"], data["password"], message.from_user.id, phone)
    except ApiError as err:
        detail = err.data.get("detail") if isinstance(err.data, dict) else err.data
        return await message.answer(t(lang, "act_error", err=detail), reply_markup=main_menu(lang))
    except Exception:
        return await message.answer(t(lang, "service_down"), reply_markup=main_menu(lang))
    await message.answer(t(lang, "act_done", until=fmt_date(mesh.get("until"))), reply_markup=main_menu(lang))


@router.message(Act.phone, F.contact)
async def phone_contact(message: Message, state: FSMContext, lang: str):
    await _finish(message, state, lang, message.contact.phone_number)


@router.message(Act.phone, F.text.in_(all_variants("act_no_phone")))
async def phone_skip(message: Message, state: FSMContext, lang: str):
    await _finish(message, state, lang, None)


@router.message(Act.phone, F.text, ~F.text.in_(MENU_TEXTS))
async def phone_typed(message: Message, state: FSMContext, lang: str):
    if not PHONE_RE.match(message.text.strip()):
        return await message.answer(t(lang, "act_bad_phone"), reply_markup=phone_kb(lang))
    await _finish(message, state, lang, message.text.strip())
