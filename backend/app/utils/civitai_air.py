"""Resolve Civitai model version IDs to AIR URNs for the Orchestration API."""

import re

import httpx

_AIR_LIKE = re.compile(r"(?:urn:)?air:", re.I)
_CIVITAI_IN_URN = re.compile(r"civitai:", re.I)
_SUPPORTED_ECOSYSTEMS = {"sd15", "sdxl", "sd3", "flux1", "illustrious", "pony", "anima"}


async def _get_air_for_model_version(client: httpx.AsyncClient, version_id: str) -> str | None:
    resp = await client.get(
        f"https://civitai.com/api/v1/model-versions/{version_id}",
        timeout=30.0,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    air = resp.json().get("air")
    if air:
        return air if str(air).startswith("urn:") else f"urn:air:{air}"
    raise ValueError(f"Civitai model-version {version_id} has no AIR field")


async def resolve_civitai_model_air(model_id: str | None) -> str | None:
    """
    Orchestration requires an AIR URN (see https://developer.civitai.com/site/guide/air).
    Frontend may send either a model-version ID or a model ID. Resolve both via
    the public Site API, then pass AIR to the Orchestration API.
    """
    if not model_id or not str(model_id).strip():
        return None

    raw = str(model_id).strip()
    if _AIR_LIKE.search(raw) or _CIVITAI_IN_URN.search(raw):
        return raw if raw.startswith("urn:") else f"urn:air:{raw.removeprefix('air:')}"

    if raw.isdigit():
        async with httpx.AsyncClient() as client:
            model_resp = await client.get(
                f"https://civitai.com/api/v1/models/{raw}",
                timeout=30.0,
            )
            if model_resp.status_code == 200:
                versions = model_resp.json().get("modelVersions") or []
                if not versions:
                    raise ValueError(f"Civitai model {raw} has no versions")
                latest_version_id = str(versions[0].get("id") or "")
                if not latest_version_id:
                    raise ValueError(f"Civitai model {raw} latest version has no id")
                air = await _get_air_for_model_version(client, latest_version_id)
                if air:
                    return air
                raise ValueError(f"Civitai model {raw} latest version {latest_version_id} has no AIR field")
            if model_resp.status_code != 404:
                model_resp.raise_for_status()

            air = await _get_air_for_model_version(client, raw)
            if air:
                return air
            raise ValueError(f"Civitai model/model-version {raw} not found")

    return raw


async def resolve_civitai_model_label(model_id: str | None) -> str:
    if not model_id or not str(model_id).strip():
        return "Civitai default"

    raw = str(model_id).strip()
    if _AIR_LIKE.search(raw) or _CIVITAI_IN_URN.search(raw):
        return raw

    if raw.isdigit():
        async with httpx.AsyncClient() as client:
            model_resp = await client.get(
                f"https://civitai.com/api/v1/models/{raw}",
                timeout=30.0,
            )
            if model_resp.status_code == 200:
                data = model_resp.json()
                model_name = data.get("name")
                versions = data.get("modelVersions") or []
                version_name = versions[0].get("name") if versions and isinstance(versions[0], dict) else None
                return " / ".join(part for part in (model_name, version_name) if part) or raw
            if model_resp.status_code != 404:
                model_resp.raise_for_status()

            version_resp = await client.get(
                f"https://civitai.com/api/v1/model-versions/{raw}",
                timeout=30.0,
            )
            if version_resp.status_code == 200:
                data = version_resp.json()
                version_name = data.get("name")
                model_name = data.get("model", {}).get("name") if isinstance(data.get("model"), dict) else None
                return " / ".join(part for part in (model_name, version_name) if part) or raw
            if version_resp.status_code != 404:
                version_resp.raise_for_status()

    return raw


def ecosystem_from_air(air: str | None) -> str:
    if not air:
        return "sdxl"
    lower = air.lower()
    raw = lower
    if raw.startswith("urn:air:"):
        raw = raw.removeprefix("urn:air:")
    elif raw.startswith("air:"):
        raw = raw.removeprefix("air:")
    ecosystem = raw.split(":", 1)[0]
    if ecosystem in {"sd1", "sd-1", "sd1.5", "sd 1.5"}:
        return "sd1"
    if ecosystem in _SUPPORTED_ECOSYSTEMS:
        return ecosystem
    return "sdxl"


def resource_type_from_air(air: str | None) -> str | None:
    if not air:
        return None
    raw = air.lower()
    if raw.startswith("urn:air:"):
        raw = raw.removeprefix("urn:air:")
    elif raw.startswith("air:"):
        raw = raw.removeprefix("air:")
    parts = raw.split(":")
    return parts[1] if len(parts) > 1 else None
