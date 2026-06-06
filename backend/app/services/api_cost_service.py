"""Provider API cost helpers (GenAPI rubles, Civitai Buzz)."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.providers.ai.base import ChatCompletionResponse


def calc_genapi_cost_rub(
    prompt_tokens: int,
    completion_tokens: int,
    *,
    settings: Settings | None = None,
) -> float:
    cfg = settings or get_settings()
    return (
        prompt_tokens / 1000 * cfg.gen_api_input_rub_per_1k_tokens
        + completion_tokens / 1000 * cfg.gen_api_output_rub_per_1k_tokens
    )


def calc_message_cost_rub(tokens_used: int, metadata: dict | None) -> float:
    meta = metadata or {}
    if meta.get("api_cost_rub") is not None:
        return float(meta["api_cost_rub"])

    prompt = int(meta.get("prompt_tokens") or 0)
    completion = int(meta.get("completion_tokens") or 0)
    if prompt or completion:
        return calc_genapi_cost_rub(prompt, completion)

    cfg = get_settings()
    if tokens_used > 0:
        return tokens_used / 1000 * cfg.gen_api_output_rub_per_1k_tokens
    return 0.0


def build_chat_message_api_meta(response: ChatCompletionResponse) -> dict[str, Any]:
    meta = dict(response.metadata or {})
    prompt = int(meta.get("prompt_tokens") or 0)
    completion = int(meta.get("completion_tokens") or 0)
    if prompt or completion:
        rub = calc_genapi_cost_rub(prompt, completion)
    else:
        cfg = get_settings()
        rub = response.tokens_used / 1000 * cfg.gen_api_output_rub_per_1k_tokens
    meta["api_cost_rub"] = round(rub, 4)
    return meta


def extract_civitai_buzz_cost(metadata: dict | None) -> int:
    meta = metadata or {}
    if meta.get("api_buzz_cost") is not None:
        return int(meta["api_buzz_cost"])

    civ = meta.get("civitai_response") or {}
    jobs = civ.get("jobs") or []
    total = 0
    for job in jobs:
        if isinstance(job, dict) and job.get("cost") is not None:
            total += int(job["cost"])
    return total


def format_rub(amount: float) -> str:
    if amount == int(amount):
        return str(int(amount))
    return f"{amount:.2f}".rstrip("0").rstrip(".")
