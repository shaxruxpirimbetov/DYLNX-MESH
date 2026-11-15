import logging
import re
import time
from datetime import date

log = logging.getLogger(__name__)

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{7,18}$")


def find_uuid(text: str | None) -> str | None:
    m = UUID_RE.search(text or "")
    return m.group(0).lower() if m else None


def short(uuid: str) -> str:
    return str(uuid)[-6:]


def fmt_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return date.fromisoformat(iso[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return iso


def is_expired(mesh: dict) -> bool:
    until = mesh.get("until")
    return bool(until) and date.fromisoformat(until[:10]) < date.today()


def ago(ts: int, lang: str) -> str:
    from texts_old import t
    mins = max(1, int((time.time() - ts) // 60))
    return t(lang, "ago_min", n=mins) if mins < 60 else t(lang, "ago_h", n=mins // 60)


def decode_qr(image_bytes: bytes) -> str | None:
    """Достаём текст из фото QR. Нужен opencv-python-headless (необязательно)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        log.warning("opencv not installed — QR photos can't be decoded")
        return None
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    for candidate in (img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)):
        try:
            data, _, _ = detector.detectAndDecode(candidate)
        except cv2.error:
            data = ""
        if data:
            return data
    return None


class RateLimiter:
    """Простейший антиспам: не чаще одного сообщения в `interval` секунд."""

    def __init__(self, interval: float):
        self.interval = interval
        self._last: dict[int, float] = {}

    def hit(self, key: int) -> bool:
        now = time.monotonic()
        if now - self._last.get(key, 0) < self.interval:
            return False
        self._last[key] = now
        return True
