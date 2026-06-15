import re
import uuid


def slugify_name(name: str) -> str:
    """URL-safe slug from display name."""
    base = name.strip().lower()
    base = re.sub(r"[^\w\s-]", "", base, flags=re.UNICODE)
    base = re.sub(r"[\s_]+", "-", base).strip("-")
    if not base:
        base = "character"
    return f"{base}-{uuid.uuid4().hex[:8]}"


def build_personality_prompt(behavior_params: list[str], *, locale: str = "ru") -> str:
    lines = [p.strip() for p in behavior_params if p and str(p).strip()]
    if not lines:
        return ""
    header = "Character behavior:" if locale == "en" else "Поведение персонажа:"
    return header + "\n" + "\n".join(f"- {line}" for line in lines)
