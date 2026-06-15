"""Pick RU/EN display strings from primary + alternative fields."""

from __future__ import annotations

import html
import re

from app.utils.locale import AppLocale, normalize_app_locale

_CYRILLIC = re.compile(r"[\u0400-\u04FF]")


def has_cyrillic(text: str | None) -> bool:
    return bool(text and _CYRILLIC.search(text))


def _preview(text: str, *, limit: int = 160) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return html.escape(raw)
    return html.escape(raw[:limit]) + "…"


def alt_lang_hint(primary: str | None) -> tuple[str, str]:
    """Return (target_lang_phrase, field_hint) for alt prompts."""
    if has_cyrillic(primary):
        return "на английском", "for EN interface"
    return "на русском", "for RU interface"


def pick_localized(primary: str | None, alt: str | None, locale: str | AppLocale) -> str:
    """Return the best label for *locale* from primary and optional alt text."""
    loc = normalize_app_locale(locale)
    primary = (primary or "").strip()
    alt = (alt or "").strip()

    if loc == "en":
        if alt and not has_cyrillic(alt):
            return alt
        if alt:
            return alt
        return primary

    # ru — prefer Cyrillic primary, else alt
    if primary and has_cyrillic(primary):
        return primary
    if alt and has_cyrillic(alt):
        return alt
    return primary or alt


def pick_localized_list(
    primary: list | None,
    alt: list | None,
    locale: str | AppLocale,
) -> list[str]:
    """Pick localized string list (e.g. behavior params)."""
    p = [str(x).strip() for x in (primary or []) if str(x).strip()]
    a = [str(x).strip() for x in (alt or []) if str(x).strip()]
    loc = normalize_app_locale(locale)
    if loc == "en" and a:
        if len(a) >= len(p):
            return a[: len(p)] if p else a
        return a + p[len(a) :]
    return p


def alt_field_prompt(primary: str, *, ru_label: str = "название", en_label: str = "name") -> str:
    lang, _ = alt_lang_hint(primary)
    label = en_label if has_cyrillic(primary) else ru_label
    return (
        f"Альтернативное <b>{label}</b> {lang} (для второго языка интерфейса).\n"
        f"<i>/skip — пропустить</i>"
    )


def alt_text_prompt(primary: str, *, field_ru: str, field_en: str) -> str:
    preview = _preview(primary)
    lang, _ = alt_lang_hint(primary)
    label = field_en if has_cyrillic(primary) else field_ru
    return (
        f"Альтернативное <b>{label}</b> {lang} (для второго языка интерфейса).\n"
        f"<i>Оригинал:</i> {preview}\n"
        f"<i>/skip — пропустить</i>"
    )


def alt_behavior_prompt(*, index: int, total: int, primary: str) -> str:
    preview = _preview(primary, limit=120)
    lang, _ = alt_lang_hint(primary)
    return (
        f"Альтернативный параметр поведения <b>{index}/{total}</b> {lang}.\n"
        f"<i>Оригинал:</i> {preview or '—'}\n"
        f"<i>/skip на первом — пропустить все {total}</i>"
    )
