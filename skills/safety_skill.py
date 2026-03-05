from __future__ import annotations
import re, json
from typing import Dict, Any, List, Optional
from config import RED_FLAG_KEYWORDS
from skills.llm_client import safe_chat
from skills.mcp_client import MCPClient

NEG_PHRASES = [
    r"(没有|并没有|并无|无|否认).{0,6}(胸痛|胸口痛|呼吸困难|气促|咯血|黑便|便血|呕血|抽搐|昏迷)",
    r"(不|未).{0,2}(胸痛|胸口痛|呼吸困难|气促|咯血|黑便|便血|呕血|抽搐|昏迷)",
    r"(胸口|胸部).{0,6}(不疼|不痛|没疼|没痛)",
]

LLM_SYS = """你是医疗安全风控审核员。
输入包含用户原话与红旗候选词。判断这些红旗是否被用户肯定/否认/不确定，以及是否需要立即就医/急诊评估。
只输出JSON：
{
  "items":[{"keyword":"胸痛","status":"affirmed|negated|uncertain","severity":"high|moderate|low","reason":"..."}],
  "overall_veto": true/false,
  "overall_reason":"..."
}
"""

def _negated(text: str, keyword: str) -> bool:
    t = text or ""
    # 关键词附近窗口
    idx = t.find(keyword)
    if idx < 0:
        return False
    win = t[max(0, idx-12):min(len(t), idx+len(keyword)+12)]
    return any(re.search(p, win) for p in NEG_PHRASES)

class SafetyAgent:
    def __init__(self):
        self.mcp = MCPClient()

    def run(self, case: Dict[str, Any], user_text: str, recent_dialog: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        t = (user_text or "").strip()
        if not t:
            return {"veto": False, "message": ""}

        # 1) MCP 关键词召回（你可继续用本地规则也行，这里走MCP更统一）
        # MCP 目前是关键词扫描，因此我们在这里做否定过滤 + LLM复核
        res = self.mcp.redflag_check(t)
        hits = res.get("reasons", []) if res.get("ok") and res.get("hit") else []
        if not hits:
            return {"veto": False, "message": ""}

        # 2) 否定过滤
        candidates = [k for k in hits if not _negated(t, k)]
        if not candidates:
            return {"veto": False, "message": ""}

        # 3) LLM 复核（避免误报）
        payload = {"user_text": t, "candidates": candidates, "recent_dialog": (recent_dialog or [])}
        fallback = json.dumps({"items":[{"keyword":k,"status":"uncertain","severity":"low","reason":"fallback"} for k in candidates],
                               "overall_veto": False, "overall_reason": ""}, ensure_ascii=False)
        out = safe_chat(
            [{"role":"system","content":LLM_SYS},{"role":"user","content":json.dumps(payload, ensure_ascii=False)}],
            fallback=fallback,
            model_env="OPENAI_MODEL",
            temperature=0.1
        )
        try:
            v = json.loads(out)
        except Exception:
            v = json.loads(fallback)

        overall_veto = bool(v.get("overall_veto", False))
        if overall_veto:
            affirmed = [it.get("keyword") for it in (v.get("items") or []) if it.get("status") == "affirmed"]
            reasons = affirmed or candidates
            case["risk"]["level"] = "high"
            case["risk"]["reasons"] = reasons
            return {"veto": True, "message": f"⚠️ 检测到可能的高风险信号：{'、'.join(reasons)}。建议尽快就医评估。"}
        return {"veto": False, "message": ""}