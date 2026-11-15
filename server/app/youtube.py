import re

_RX = re.compile(r"(?:youtu\.be/|[?&]v=|/embed/|/shorts/|/live/)([\w-]{11})")


def youtube_id(url_or_id: str | None) -> str | None:
    if not url_or_id:
        return None
    s = url_or_id.strip()
    if re.fullmatch(r"[\w-]{11}", s):
        return s
    m = _RX.search(s)
    return m.group(1) if m else None
