"""Shared helpers for parsing heterogeneous image-generation API responses.

Different providers (Civitai, gen-api / Z-Image, Fal, Replicate, etc.) all
return JSON with the image URL hidden in slightly different shapes. This
module centralises the "walk the JSON, find me the first http(s) URL that
looks like an image" logic so providers don't have to reinvent it.
"""

from typing import Any

_IMAGE_URL_KEYS = ("url", "imageUrl", "blobUrl", "previewUrl", "downloadUrl")
_IMAGE_LIST_KEYS = ("jobs", "images", "blobs", "outputs", "data")


def extract_image_url(response: Any) -> str | None:
    """Recursively walk an arbitrary JSON-like value and return the first
    image URL that looks like http(s)://...

    Returns ``None`` if nothing is found. The same value is returned for
    strings, dicts (with various common keys), lists, pydantic models, etc.
    """
    # 1) bare string
    if isinstance(response, str):
        return response if response.startswith(("http://", "https://")) else None

    # 2) pydantic-style model
    if hasattr(response, "model_dump"):
        found = extract_image_url(response.model_dump())
        if found:
            return found

    # 3) dict — known keys first, then collections, then recursive
    if isinstance(response, dict):
        for key in _IMAGE_URL_KEYS:
            value = response.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value

        result = response.get("result")
        if result:
            found = extract_image_url(result)
            if found:
                return found

        for key in _IMAGE_LIST_KEYS:
            collection = response.get(key)
            if isinstance(collection, list):
                for item in collection:
                    found = extract_image_url(item)
                    if found:
                        return found

        for value in response.values():
            if isinstance(value, (dict, list)):
                found = extract_image_url(value)
                if found:
                    return found

    # 4) list
    if isinstance(response, list):
        for item in response:
            found = extract_image_url(item)
            if found:
                return found

    # 5) object with attribute access (e.g. pydantic without model_dump)
    for key in ("url", "imageUrl", "blobUrl", "previewUrl", "downloadUrl", "result"):
        if hasattr(response, key):
            try:
                value = getattr(response, key)
            except Exception:
                continue
            found = extract_image_url(value)
            if found:
                return found

    return None
