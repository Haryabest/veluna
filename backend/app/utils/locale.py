"""App UI locale helpers (ru / en only)."""

from typing import Literal

AppLocale = Literal["ru", "en"]

SUPPORTED_LOCALES: frozenset[str] = frozenset({"ru", "en"})


def normalize_app_locale(value: str | None, *, default: str = "ru") -> AppLocale:
    if not value:
        return default  # type: ignore[return-value]
    code = value.strip().lower().replace("_", "-")
    if code in ("ru", "ru-ru", "be", "uk", "kk"):
        return "ru"
    return "en"


def locale_from_telegram(language_code: str | None) -> AppLocale:
    return normalize_app_locale(language_code, default="en")
