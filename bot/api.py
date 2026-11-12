"""Клиент к бэкенду Mesh (Django DRF + SimpleJWT)."""
import asyncio
import json
import logging
from typing import Any

import aiohttp

from config import config

log = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status: int, data: Any):
        super().__init__(f"API {status}: {data}")
        self.status = status
        self.data = data


async def _read(r: aiohttp.ClientResponse):
    """JSON из ответа. Если пришёл HTML (404/500/ALLOWED_HOSTS) — понятная ошибка вместо JSONDecodeError."""
    if r.status == 204:
        return None
    text = await r.text()
    try:
        return json.loads(text) if text else None
    except ValueError:
        snippet = " ".join(text.split())[:160]
        raise ApiError(r.status, f"бэкенд вернул не JSON ({r.method} {r.url}): {snippet}")


class MeshAPI:
    def __init__(self, base_url: str, username: str, password: str):
        self.base = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._access: str | None = None
        self._refresh: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._auth_lock = asyncio.Lock()

    # ---------- infra ----------
    async def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _login(self):
        s = await self.session()
        # сначала пробуем refresh, потом полноценный логин
        if self._refresh:
            async with s.post(f"{self.base}/api/refresh/", json={"refresh": self._refresh}) as r:
                if r.status == 200:
                    self._access = (await _read(r))["access"]
                    return
        async with s.post(f"{self.base}/api/token/",
                          json={"username": self.username, "password": self.password}) as r:
            data = await _read(r)
            if r.status != 200:
                raise ApiError(r.status, data)
            self._access, self._refresh = data["access"], data["refresh"]
            log.info("Logged in to Mesh API as %s", self.username)

    async def request(self, method: str, path: str, *, json: Any = None, params: dict | None = None,
                      ok: tuple[int, ...] = (200, 201, 204)) -> Any:
        s = await self.session()
        for attempt in range(2):
            if not self._access:
                async with self._auth_lock:
                    if not self._access:
                        await self._login()
            headers = {"Authorization": f"Bearer {self._access}"}
            async with s.request(method, f"{self.base}{path}", json=json, params=params, headers=headers) as r:
                if r.status == 401 and attempt == 0:
                    self._access = None
                    continue
                data = await _read(r)
                if r.status not in ok:
                    raise ApiError(r.status, data)
                return data

    async def check(self):
        """Проверка при старте: адрес верный, логин работает, аккаунт staff."""
        await self._login()
        me = await self.request("GET", "/api/user/me/")
        if not me.get("is_staff"):
            raise ApiError(403, f"аккаунт {self.username} без is_staff — боту нужен staff")
        await self.request("GET", "/api/message/", params={"page_size": 1})
        return me

    # ---------- mesh ----------
    async def get_mesh(self, uuid: str) -> dict | None:
        try:
            return await self.request("GET", f"/api/mesh/uuid/{uuid}/")
        except ApiError as e:
            if e.status == 404:
                return None
            raise

    async def update_mesh(self, uuid: str, data: dict) -> dict:
        return await self.request("PATCH", f"/api/mesh/uuid/{uuid}/", json=data)

    async def activate(self, uuid: str, password: str, telegram_id: int, phone: str | None) -> dict:
        return await self.request("PATCH", f"/api/mesh/activate/{uuid}/", json={
            "password": password, "telegram_id": telegram_id, "phone": phone,
        })

    async def meshes(self, **filters) -> list[dict]:
        out, page = [], 1
        while True:
            data = await self.request("GET", "/api/mesh/", params={**filters, "page": page, "page_size": 200})
            out.extend(data["results"])
            if not data.get("next"):
                return out
            page += 1

    async def my_meshes(self, telegram_id: int) -> list[dict]:
        return await self.meshes(telegram_id=telegram_id)

    async def stats(self) -> dict:
        return await self.request("GET", "/api/mesh/stats/")

    # ---------- messages ----------
    async def create_message(self, mesh_id: int, telegram_id: int, text: str) -> dict:
        return await self.request("POST", "/api/message/", json={
            "mesh": mesh_id, "telegram_id": telegram_id, "message": text[:4000],
        })

    async def messages_after(self, after_id: int) -> list[dict]:
        out, page = [], 1
        while True:
            data = await self.request("GET", "/api/message/",
                                      params={"after_id": after_id, "page": page, "page_size": 100})
            out.extend(data["results"])
            if not data.get("next") or page >= 10:
                return out
            page += 1

    async def last_message_id(self) -> int:
        data = await self.request("GET", "/api/message/", params={"page_size": 1})
        return data["results"][0]["id"] if data["results"] else 0


api = MeshAPI(config.api_url, config.api_username, config.api_password)
