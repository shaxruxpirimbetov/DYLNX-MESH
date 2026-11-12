import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> set[int]:
    return {int(x) for x in raw.replace(" ", "").split(",") if x.strip().lstrip("-").isdigit()}


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    # Адрес бэкенда Mesh (BACKEND_HERE), без слэша в конце
    api_url: str = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
    # Аккаунт бота на бэкенде: is_staff=True (role LISA по умолчанию)
    api_username: str = os.getenv("API_USERNAME", "")
    api_password: str = os.getenv("API_PASSWORD", "")

    admin_ids: set[int] = field(default_factory=lambda: _ids(os.getenv("ADMIN_IDS", "")))
    buy_url: str = os.getenv("BUY_URL", "")
    support_username: str = os.getenv("SUPPORT_USERNAME", "").lstrip("@")

    db_path: str = os.getenv("DB_PATH", "mesh_bot.sqlite3")
    poll_interval: float = float(os.getenv("POLL_INTERVAL", "3"))
    chat_ttl_hours: int = int(os.getenv("CHAT_TTL_HOURS", "24"))
    expiry_remind_days: int = int(os.getenv("EXPIRY_REMIND_DAYS", "3"))


config = Config()
BRAND = "Mesh - DYLNX"
