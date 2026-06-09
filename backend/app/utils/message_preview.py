import re

_IMAGE_MESSAGE_RE = re.compile(r"^!\[[^\]]*\]\([^)]+\)\s*$")


def format_message_preview(content: str | None, *, max_len: int = 120) -> str | None:
    text = (content or "").strip()
    if not text:
        return None
    if _IMAGE_MESSAGE_RE.match(text):
        return "фотография"
    if len(text) > max_len:
        return text[:max_len]
    return text
