"""Локальное состояние бота (SQLite): языки, анонимные диалоги, блокировки, маршрутизация ответов."""
import time

import aiosqlite

from config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id       INTEGER PRIMARY KEY,
    lang        TEXT    NOT NULL DEFAULT 'ru',
    active_conv INTEGER,
    created_at  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mesh_id    INTEGER NOT NULL,
    mesh_uuid  TEXT    NOT NULL,
    owner_tg   INTEGER NOT NULL,
    guest_tg   INTEGER NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'open',
    created_at INTEGER NOT NULL,
    last_at    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS conv_guest ON conversations(guest_tg, status);
CREATE INDEX IF NOT EXISTS conv_owner ON conversations(owner_tg, status);
CREATE TABLE IF NOT EXISTS blocks (
    owner_tg INTEGER NOT NULL,
    guest_tg INTEGER NOT NULL,
    PRIMARY KEY (owner_tg, guest_tg)
);
CREATE TABLE IF NOT EXISTS msg_map (
    chat_id    INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    conv_id    INTEGER NOT NULL,
    PRIMARY KEY (chat_id, message_id)
);
CREATE TABLE IF NOT EXISTS sent_ids (api_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS attempts (tg_id INTEGER NOT NULL, ts INTEGER NOT NULL);
"""


class DB:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def _one(self, sql, *args):
        async with self.conn.execute(sql, args) as cur:
            return await cur.fetchone()

    async def _all(self, sql, *args):
        async with self.conn.execute(sql, args) as cur:
            return await cur.fetchall()

    async def _exec(self, sql, *args):
        cur = await self.conn.execute(sql, args)
        await self.conn.commit()
        return cur

    # ---------- users ----------
    async def ensure_user(self, tg_id: int, language_code: str | None) -> str:
        row = await self._one("SELECT lang FROM users WHERE tg_id=?", tg_id)
        if row:
            return row["lang"]
        lang = "uz" if (language_code or "").startswith("uz") else "ru"
        await self._exec("INSERT INTO users(tg_id, lang, created_at) VALUES (?,?,?)", tg_id, lang, int(time.time()))
        return lang

    async def get_lang(self, tg_id: int) -> str:
        row = await self._one("SELECT lang FROM users WHERE tg_id=?", tg_id)
        return row["lang"] if row else "ru"

    async def set_lang(self, tg_id: int, lang: str):
        await self._exec("UPDATE users SET lang=? WHERE tg_id=?", lang, tg_id)

    async def set_active_conv(self, tg_id: int, conv_id: int | None):
        await self._exec("UPDATE users SET active_conv=? WHERE tg_id=?", conv_id, tg_id)

    async def get_active_conv(self, tg_id: int):
        row = await self._one("SELECT active_conv FROM users WHERE tg_id=?", tg_id)
        if not row or not row["active_conv"]:
            return None
        conv = await self.get_conv(row["active_conv"])
        if conv and conv["status"] == "open" and tg_id in (conv["owner_tg"], conv["guest_tg"]):
            return conv
        return None

    # ---------- conversations ----------
    async def get_conv(self, conv_id: int):
        return await self._one("SELECT * FROM conversations WHERE id=?", conv_id)

    async def open_conv(self, mesh_id: int, mesh_uuid: str, owner_tg: int, guest_tg: int):
        """Найти открытый диалог гостя по этому стикеру или создать новый. -> (conv, created)"""
        row = await self._one(
            "SELECT * FROM conversations WHERE mesh_uuid=? AND guest_tg=? AND owner_tg=? AND status='open'",
            mesh_uuid, guest_tg, owner_tg)
        if row:
            return row, False
        now = int(time.time())
        cur = await self._exec(
            "INSERT INTO conversations(mesh_id, mesh_uuid, owner_tg, guest_tg, created_at, last_at) "
            "VALUES (?,?,?,?,?,?)", mesh_id, mesh_uuid, owner_tg, guest_tg, now, now)
        return await self.get_conv(cur.lastrowid), True

    async def touch_conv(self, conv_id: int):
        await self._exec("UPDATE conversations SET last_at=? WHERE id=?", int(time.time()), conv_id)

    async def close_conv(self, conv_id: int):
        await self._exec("UPDATE conversations SET status='closed' WHERE id=?", conv_id)

    async def open_convs_for(self, tg_id: int):
        return await self._all(
            "SELECT * FROM conversations WHERE status='open' AND (owner_tg=? OR guest_tg=?) "
            "ORDER BY last_at DESC LIMIT 20", tg_id, tg_id)

    async def close_stale(self, ttl_seconds: int) -> int:
        cur = await self._exec("UPDATE conversations SET status='closed' WHERE status='open' AND last_at<?",
                               int(time.time()) - ttl_seconds)
        return cur.rowcount

    # ---------- reply routing ----------
    async def map_msg(self, chat_id: int, message_id: int, conv_id: int):
        await self._exec("INSERT OR REPLACE INTO msg_map VALUES (?,?,?)", chat_id, message_id, conv_id)

    async def conv_by_msg(self, chat_id: int, message_id: int):
        row = await self._one("SELECT conv_id FROM msg_map WHERE chat_id=? AND message_id=?", chat_id, message_id)
        return await self.get_conv(row["conv_id"]) if row else None

    # ---------- blocks ----------
    async def block(self, owner_tg: int, guest_tg: int):
        await self._exec("INSERT OR IGNORE INTO blocks VALUES (?,?)", owner_tg, guest_tg)

    async def unblock(self, owner_tg: int, guest_tg: int):
        await self._exec("DELETE FROM blocks WHERE owner_tg=? AND guest_tg=?", owner_tg, guest_tg)

    async def is_blocked(self, owner_tg: int, guest_tg: int) -> bool:
        return bool(await self._one("SELECT 1 FROM blocks WHERE owner_tg=? AND guest_tg=?", owner_tg, guest_tg))

    # ---------- poller bookkeeping ----------
    async def mark_sent(self, api_id: int):
        await self._exec("INSERT OR IGNORE INTO sent_ids VALUES (?)", api_id)

    async def pop_sent(self, api_id: int) -> bool:
        cur = await self._exec("DELETE FROM sent_ids WHERE api_id=?", api_id)
        return cur.rowcount > 0

    async def kv_get(self, key: str) -> str | None:
        row = await self._one("SELECT value FROM kv WHERE key=?", key)
        return row["value"] if row else None

    async def kv_set(self, key: str, value: str):
        await self._exec("INSERT OR REPLACE INTO kv VALUES (?,?)", key, value)

    # ---------- anti brute-force активации ----------
    async def add_attempt(self, tg_id: int):
        await self._exec("INSERT INTO attempts VALUES (?,?)", tg_id, int(time.time()))

    async def attempts_recent(self, tg_id: int, window: int = 900) -> int:
        await self._exec("DELETE FROM attempts WHERE ts<?", int(time.time()) - 86400)
        row = await self._one("SELECT COUNT(*) c FROM attempts WHERE tg_id=? AND ts>=?",
                              tg_id, int(time.time()) - window)
        return row["c"]


db = DB(config.db_path)
