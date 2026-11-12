"""«Мои стикеры»: список, карточка, номер показать/скрыть, QR, отвязка."""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton as IB, InlineKeyboardMarkup, Message

from api import api
from keyboards import is_public_url, main_menu, share_phone_only_kb
from texts import MENU_TEXTS, all_variants, t
from utils import fmt_date, is_expired, short

log = logging.getLogger(__name__)
router = Router(name="meshes")


class PhoneState(StatesGroup):
    wait = State()


def list_kb(lang: str, meshes: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IB(text=t(lang, "my_row", short=short(m["uuid"]), until=fmt_date(m["until"])), callback_data=f"m:{m['uuid']}")]
        for m in meshes
    ])


def card(lang: str, m: dict) -> tuple[str, InlineKeyboardMarkup]:
    status = t(lang, "st_expired") if is_expired(m) else t(lang, "st_active" if m["is_active"] else "st_off")
    text = t(lang, "card", uuid=m["uuid"], status=status, until=fmt_date(m["until"]),
             phone=m.get("phone") or t(lang, "phone_hidden"), count=m.get("messages_count", 0))
    rows = [[IB(text=t(lang, "b_phone_hide") if m.get("phone") else t(lang, "b_phone_show"),
                callback_data=f"mp:{m['uuid']}:{'hide' if m.get('phone') else 'show'}")]]
    second = [IB(text=t(lang, "b_qr"), callback_data=f"mq:{m['uuid']}")]
    if is_public_url(m.get("url")):
        second.insert(0, IB(text=t(lang, "b_open_page"), url=m["url"]))
    rows.append(second)
    rows.append([IB(text=t(lang, "b_unbind"), callback_data=f"mu:{m['uuid']}")])
    rows.append([IB(text=t(lang, "btn_back"), callback_data="ml")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


async def _own_mesh(cb: CallbackQuery, uuid: str) -> dict | None:
    """Мешаем чужим трогать стикер: проверяем, что он реально принадлежит нажавшему."""
    mesh = await api.get_mesh(uuid)
    if not mesh or str(mesh.get("telegram_id")) != str(cb.from_user.id):
        await cb.answer("⛔️", show_alert=True)
        return None
    return mesh


@router.message(Command("my"))
@router.message(F.text.in_(all_variants("btn_my")))
async def my_meshes(message: Message, state: FSMContext, lang: str):
    await state.clear()
    try:
        meshes = await api.my_meshes(message.from_user.id)
    except Exception:
        return await message.answer(t(lang, "service_down"), reply_markup=main_menu(lang))
    if not meshes:
        return await message.answer(t(lang, "my_empty"), reply_markup=main_menu(lang))
    if len(meshes) == 1:
        text, kb = card(lang, meshes[0])
        return await message.answer(text, reply_markup=kb)
    await message.answer(t(lang, "my_title"), reply_markup=list_kb(lang, meshes))


@router.callback_query(F.data == "ml")
async def cb_list(cb: CallbackQuery, lang: str):
    meshes = await api.my_meshes(cb.from_user.id)
    if not meshes:
        await cb.message.edit_text(t(lang, "my_empty"))
    else:
        await cb.message.edit_text(t(lang, "my_title"), reply_markup=list_kb(lang, meshes))
    await cb.answer()


@router.callback_query(F.data.startswith("m:"))
async def cb_card(cb: CallbackQuery, lang: str):
    mesh = await _own_mesh(cb, cb.data[2:])
    if not mesh:
        return
    text, kb = card(lang, mesh)
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("mp:"))
async def cb_phone(cb: CallbackQuery, state: FSMContext, lang: str):
    _, uuid, action = cb.data.split(":")
    mesh = await _own_mesh(cb, uuid)
    if not mesh:
        return
    if action == "hide":
        mesh = await api.update_mesh(uuid, {"phone": None})
        text, kb = card(lang, mesh)
        await cb.message.edit_text(text, reply_markup=kb)
        return await cb.answer(t(lang, "phone_hidden_ok"))
    await state.set_state(PhoneState.wait)
    await state.update_data(uuid=uuid)
    await cb.message.answer(t(lang, "phone_ask"), reply_markup=share_phone_only_kb(lang))
    await cb.answer()


@router.message(PhoneState.wait, F.contact)
async def phone_received(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    await state.clear()
    mesh = await api.get_mesh(data["uuid"])
    if not mesh or str(mesh.get("telegram_id")) != str(message.from_user.id):
        return await message.answer("⛔️", reply_markup=main_menu(lang))
    await api.update_mesh(data["uuid"], {"phone": message.contact.phone_number})
    await message.answer(t(lang, "phone_saved"), reply_markup=main_menu(lang))


@router.message(PhoneState.wait, ~F.text.in_(MENU_TEXTS))
async def phone_wrong(message: Message, lang: str):
    await message.answer(t(lang, "phone_ask"), reply_markup=share_phone_only_kb(lang))


@router.callback_query(F.data.startswith("mq:"))
async def cb_qr(cb: CallbackQuery, lang: str):
    mesh = await _own_mesh(cb, cb.data[3:])
    if not mesh:
        return
    if not mesh.get("qrcode"):
        return await cb.answer(t(lang, "no_qr"), show_alert=True)
    try:
        await cb.message.answer_photo(mesh["qrcode"], caption=f"Mesh - DYLNX · <code>{mesh['uuid']}</code>")
    except Exception:
        await cb.message.answer(mesh["qrcode"])
    await cb.answer()


@router.callback_query(F.data.startswith("mu:"))
async def cb_unbind_ask(cb: CallbackQuery, lang: str):
    uuid = cb.data[3:]
    if not await _own_mesh(cb, uuid):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        IB(text=t(lang, "b_yes"), callback_data=f"muy:{uuid}"),
        IB(text=t(lang, "btn_back"), callback_data=f"m:{uuid}"),
    ]])
    await cb.message.edit_text(t(lang, "unbind_confirm"), reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("muy:"))
async def cb_unbind(cb: CallbackQuery, lang: str):
    uuid = cb.data[4:]
    if not await _own_mesh(cb, uuid):
        return
    await api.update_mesh(uuid, {"is_active": False, "telegram_id": None, "phone": None})
    await cb.message.edit_text(t(lang, "unbound"))
    await cb.answer()
