"""Bot UI strings (ru / en)."""

from app.utils.locale import AppLocale, normalize_app_locale

TEXTS: dict[str, dict[str, str]] = {
    "welcome": {
        "ru": "Добро пожаловать в Veluna — AI-компаньоны в аниме-стиле.",
        "en": "Welcome to Veluna — anime-style AI companions.",
    },
    "choose_language": {
        "ru": "Выберите язык интерфейса:",
        "en": "Choose your interface language:",
    },
    "language_saved": {
        "ru": "Язык сохранён: Русский 🇷🇺",
        "en": "Language saved: English 🇬🇧",
    },
    "language_saved_en": {
        "ru": "Язык сохранён: English 🇬🇧",
        "en": "Language saved: English 🇬🇧",
    },
    "open_veluna": {
        "ru": "Открыть Veluna",
        "en": "Open Veluna",
    },
    "switch_language": {
        "ru": "🌐 Переключить язык",
        "en": "🌐 Switch language",
    },
    "menu_open_veluna": {
        "ru": "Открыть Veluna",
        "en": "Open Veluna",
    },
    "menu_hint": {
        "ru": "Меню бота:",
        "en": "Bot menu:",
    },
}


def t(key: str, locale: str | AppLocale) -> str:
    loc = normalize_app_locale(locale)
    bucket = TEXTS.get(key, {})
    return bucket.get(loc) or bucket.get("ru") or key


def user_locale(user) -> AppLocale:
    if user is None:
        return "ru"
    return normalize_app_locale(getattr(user, "language_code", None))
