from aiogram.types import (InlineKeyboardButton as IB, InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup)

from config import config
from texts import QUICK_KEYS, t


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t(lang, "btn_my")), KeyboardButton(text=t(lang, "btn_chats"))],
        [KeyboardButton(text=t(lang, "btn_activate")), KeyboardButton(text=t(lang, "btn_buy"))],
        [KeyboardButton(text=t(lang, "btn_help")), KeyboardButton(text=t(lang, "btn_lang"))],
    ])


def cancel_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text=t(lang, "btn_cancel"))]])


def phone_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[
        [KeyboardButton(text=t(lang, "act_share_phone"), request_contact=True)],
        [KeyboardButton(text=t(lang, "act_no_phone"))],
        [KeyboardButton(text=t(lang, "btn_cancel"))],
    ])


def share_phone_only_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[
        [KeyboardButton(text=t(lang, "act_share_phone"), request_contact=True)],
        [KeyboardButton(text=t(lang, "btn_cancel"))],
    ])


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        IB(text="🇷🇺 Русский", callback_data="lang:ru"),
        IB(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
    ]])


def quick_kb(lang: str, conv_id: int) -> InlineKeyboardMarkup:
    rows = [[IB(text=t(lang, f"q_{k}"), callback_data=f"q:{conv_id}:{k}")] for k in QUICK_KEYS]
    rows.append([IB(text=t(lang, "q_custom"), callback_data=f"q:{conv_id}:custom")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def owner_msg_kb(lang: str, conv_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IB(text=t(lang, "b_reply"), callback_data=f"rep:{conv_id}"),
         IB(text=t(lang, "b_omw"), callback_data=f"omw:{conv_id}")],
        [IB(text=t(lang, "b_block"), callback_data=f"blk:{conv_id}"),
         IB(text=t(lang, "b_end"), callback_data=f"end:{conv_id}")],
    ])


def guest_msg_kb(lang: str, conv_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        IB(text=t(lang, "b_reply"), callback_data=f"rep:{conv_id}"),
        IB(text=t(lang, "b_end"), callback_data=f"end:{conv_id}"),
    ]])


def unblock_kb(lang: str, conv_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[IB(text=t(lang, "b_unblock"), callback_data=f"unb:{conv_id}")]])


def activate_kb(lang: str, uuid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        IB(text=t(lang, "btn_activate"), callback_data=f"act:{uuid}")]])


def buy_kb(lang: str) -> InlineKeyboardMarkup | None:
    rows = []
    if config.buy_url:
        rows.append([IB(text=t(lang, "buy_btn"), url=config.buy_url)])
    if config.support_username:
        rows.append([IB(text=t(lang, "support_btn"), url=f"https://t.me/{config.support_username}")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def is_public_url(url: str | None) -> bool:
    # Telegram не принимает localhost/127.0.0.1 в url-кнопках
    return bool(url) and url.startswith("https://")
