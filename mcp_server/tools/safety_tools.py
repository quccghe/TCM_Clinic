from typing import Dict, Any
from config import RED_FLAG_KEYWORDS

def redflag_check(text: str) -> Dict[str, Any]:
    t = text or ""
    hits = [k for k in RED_FLAG_KEYWORDS if k in t]
    return {"ok": True, "hit": len(hits) > 0, "reasons": hits}