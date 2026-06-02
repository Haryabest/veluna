import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TelegramAuthError(Exception):
    pass


def validate_telegram_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """Validate Telegram WebApp initData per official spec."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise TelegramAuthError("Telegram bot token not configured")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("Missing hash in initData")

    auth_date = parsed.get("auth_date")
    if auth_date:
        age = time.time() - int(auth_date)
        if age > max_age_seconds:
            raise TelegramAuthError("initData expired")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode(),
        hashlib.sha256,
    ).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise TelegramAuthError("Invalid initData hash")

    user_data = parsed.get("user")
    if user_data:
        parsed["user"] = json.loads(user_data)

    return parsed
