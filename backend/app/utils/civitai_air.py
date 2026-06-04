"""Resolve Civitai model version IDs to AIR URNs for the Orchestration API."""

import re

import httpx

_AIR_LIKE = re.compile(r"(?:urn:)?air:", re.I)
_CIVITAI_IN_URN = re.compile(r"civitai:", re.I)


async def resolve_civitai_model_air(model_id: str | None) -> str | None:
    """
    Orchestration requires an AIR URN (see https://developer.civitai.com/site/guide/air).
    Frontend sends model-versions id (e.g. 934764); resolve via public Site API.
    """
    if not model_id or not str(model_id).strip():
        return None

    raw = str(model_id).strip()
    if _AIR_LIKE.search(raw) or _CIVITAI_IN_URN.search(raw):
        return raw if raw.startswith("urn:") else f"urn:air:{raw.removeprefix('air:')}"

    if raw.isdigit():
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://civitai.com/api/v1/model-versions/{raw}",
                timeout=30.0,
            )
            resp.raise_for_status()
            air = resp.json().get("air")
            if air:
                return air if str(air).startswith("urn:") else f"urn:air:{air}"
            raise ValueError(f"Civitai model-version {raw} has no AIR field")

    return raw


def ecosystem_from_air(air: str | None) -> str:
    if not air:
        return "sdxl"
    lower = air.lower()
    if ":sd1:" in lower or lower.startswith("sd1:"):
        return "sd1"
    if ":sdxl:" in lower or lower.startswith("sdxl:"):
        return "sdxl"
    if ":sd3:" in lower:
        return "sd3"
    if ":flux" in lower:
        return "flux1"
    return "sdxl"
