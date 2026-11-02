
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

try:
    ADMIN_IDS = {
        int(raw.strip())
        for raw in os.getenv("ADMIN_IDS", "").split(",")
        if raw.strip()
    }
except ValueError as exc:
    raise RuntimeError(
        "ADMIN_IDS: укажи Telegram ID через запятую"
    ) from exc
