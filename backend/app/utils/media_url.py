import re

_LEGACY_PREFIXES = (
    "http://localhost:9000/veluna/",
    "http://127.0.0.1:9000/veluna/",
    "https://localhost:9000/veluna/",
)


def normalize_media_url(url: str | None) -> str | None:
    if not url:
        return None
    for prefix in _LEGACY_PREFIXES:
        if url.startswith(prefix):
            return "/media/" + url[len(prefix) :]
    m = re.match(r"https?://[^/]+/veluna/(.+)", url)
    if m:
        return f"/media/{m.group(1)}"
    return url
