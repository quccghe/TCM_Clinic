import re

DECLINE_PATTERNS = [
    r"没有(了)?$",
    r"没了$",
    r"不知道$",
    r"不清楚$",
    r"记不清$",
    r"没有更多$",
    r"就这样$",
    r"随便$",
]

def is_decline(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return any(re.search(p, t) for p in DECLINE_PATTERNS)