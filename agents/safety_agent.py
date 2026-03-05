# agents/safety_agent.py
from __future__ import annotations

import re
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

from config import RED_FLAG_KEYWORDS
from skills.llm_client import safe_chat


# -----------------------------
# Safety NLU utilities
# -----------------------------

_NEG_PREFIX_PATTERNS = [
    r"无", r"没有", r"没", r"不", r"未", r"否认", r"从未", r"并无", r"并没有", r"不是"
]

# 常见“否定 + 症状”的固定表达（覆盖率很高）
_NEG_PHRASE_PATTERNS = [
    r"(没有|并没有|并无|无|否认).{0,6}(胸痛|胸口痛|胸闷|气短|呼吸困难|咯血|晕厥|黑便|便血|呕血|抽搐|昏迷)",
    r"(不|未).{0,2}(胸痛|胸口痛|胸闷|气短|呼吸困难|咯血|晕厥|黑便|便血|呕血|抽搐|昏迷)",
    r"(胸口|胸部|胸前).{0,6}(不疼|不痛|不难受|没疼|没痛)",
]

# 一些“弱风险/需要澄清”的表达（不直接一票否决）
_UNCERTAIN_PATTERNS = [
    r"好像", r"可能", r"不确定", r"说不清", r"大概", r"有点", r"偶尔", r"时有时无"
]


@dataclass
class Hit:
    keyword: str
    span: Tuple[int, int]
    context: str
    negated: bool
    uncertain: bool


def _find_keyword_spans(text: str, keyword: str) -> List[Tuple[int, int]]:
    spans = []
    start = 0
    while True:
        idx = text.find(keyword, start)
        if idx < 0:
            break
        spans.append((idx, idx + len(keyword)))
        start = idx + len(keyword)
    return spans


def _window(text: str, span: Tuple[int, int], w: int = 14) -> str:
    s, e = span
    left = max(0, s - w)
    right = min(len(text), e + w)
    return text[left:right]


def _is_negated(text: str, span: Tuple[int, int]) -> bool:
    """Rule-based negation detection around the span."""
    ctx = _window(text, span, w=18)

    # strong phrase patterns
    for pat in _NEG_PHRASE_PATTERNS:
        if re.search(pat, ctx):
            return True

    # generic prefix negation close to the keyword
    # e.g. "不胸痛"(rare) / "没有胸痛" / "胸痛没有"(rare)
    # we check within 0~6 chars left side
    s, _ = span
    left = text[max(0, s - 8):s]
    if re.search(r"(" + "|".join(_NEG_PREFIX_PATTERNS) + r")\s*$", left):
        return True

    return False


def _is_uncertain(text: str, span: Tuple[int, int]) -> bool:
    ctx = _window(text, span, w=18)
    return any(re.search(pat, ctx) for pat in _UNCERTAIN_PATTERNS)


def extract_hits(text: str, keywords: List[str]) -> List[Hit]:
    t = text or ""
    hits: List[Hit] = []
    for kw in keywords:
        for sp in _find_keyword_spans(t, kw):
            ctx = _window(t, sp, w=22)
            hits.append(Hit(
                keyword=kw,
                span=sp,
                context=ctx,
                negated=_is_negated(t, sp),
                uncertain=_is_uncertain(t, sp)
            ))
    # de-duplicate by (keyword, span)
    uniq = {}
    for h in hits:
        uniq[(h.keyword, h.span)] = h
    return list(uniq.values())


# -----------------------------
# LLM verifier (3rd layer)
# -----------------------------

_LLM_SYS = """你是医疗安全风控审核员。
任务：判断用户文本中提到的“红旗症状”是否真实存在（肯定/否定/不确定），以及是否需要“立即就医/急诊评估”。

你会收到：
- user_text：用户原话
- candidates：系统检测到的红旗关键词列表（每个含关键词+上下文片段+是否被规则判定为否定/不确定）

请你输出严格JSON（只输出JSON）：
{
  "items": [
    {
      "keyword": "胸痛",
      "status": "affirmed|negated|uncertain",
      "severity": "high|moderate|low",
      "reason": "一句话说明（引用用户表述，不要编造）"
    }
  ],
  "overall_veto": true/false,
  "overall_reason": "若veto=true，给一句话原因"
}

规则：
- 若用户明确否认：status=negated
- 若用户明确描述存在且严重：status=affirmed + severity=high，并 overall_veto=true
- 若只是轻微/不典型：可moderate，不一定veto
- 不要凭空推断不存在的信息
"""


def llm_verify(user_text: str, candidates: List[Hit]) -> Dict[str, Any]:
    payload = {
        "user_text": user_text,
        "candidates": [
            {
                "keyword": h.keyword,
                "context": h.context,
                "rule_negated": h.negated,
                "rule_uncertain": h.uncertain
            }
            for h in candidates
        ]
    }

    fallback = json.dumps({
        "items": [
            {"keyword": h.keyword, "status": ("negated" if h.negated else "uncertain"), "severity": "low",
             "reason": "LLM不可用，按规则判断"}
            for h in candidates
        ],
        "overall_veto": False,
        "overall_reason": ""
    }, ensure_ascii=False)

    out = safe_chat(
        [{"role": "system", "content": _LLM_SYS},
         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        fallback=fallback,
        model_env="OPENAI_MODEL",
        temperature=0.1
    )
    try:
        data = json.loads(out)
        return data if isinstance(data, dict) else json.loads(fallback)
    except Exception:
        return json.loads(fallback)


# -----------------------------
# SafetyAgent
# -----------------------------

class SafetyAgent:
    """
    三级安全风控：
    1) 关键词召回（高召回）
    2) 否定/不确定规则过滤（减少误报）
    3) LLM语义复核（对不确定情况提精度）
    """

    def __init__(self, keywords: Optional[List[str]] = None):
        self.keywords = keywords or RED_FLAG_KEYWORDS

    def run(self, case: Dict[str, Any], user_text: str, recent_dialog: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        t = (user_text or "").strip()
        if not t:
            return {"veto": False, "message": ""}

        # 1) rule recall
        hits = extract_hits(t, self.keywords)
        if not hits:
            return {"veto": False, "message": ""}

        # 2) filter out clearly negated hits
        affirmed_or_uncertain = [h for h in hits if not h.negated]

        # If everything is negated -> safe (no veto)
        if not affirmed_or_uncertain:
            return {"veto": False, "message": ""}

        # 2.5) if only weak/uncertain mentions, use LLM verify
        need_llm = any(h.uncertain for h in affirmed_or_uncertain) or len(affirmed_or_uncertain) >= 1

        # 3) LLM verify
        if need_llm:
            verify = llm_verify(t, affirmed_or_uncertain)

            # Decide veto
            overall_veto = bool(verify.get("overall_veto", False))
            items = verify.get("items", []) or []

            # If LLM didn't set overall_veto, we compute conservative veto:
            # any affirmed+high => veto
            if not overall_veto:
                for it in items:
                    if it.get("status") == "affirmed" and it.get("severity") == "high":
                        overall_veto = True
                        break

            if overall_veto:
                reasons = []
                for it in items:
                    if it.get("status") == "affirmed":
                        reasons.append(it.get("keyword"))
                if not reasons:
                    # fallback reason list
                    reasons = [h.keyword for h in affirmed_or_uncertain]

                case["risk"]["level"] = "high"
                case["risk"]["reasons"] = reasons

                msg = f"⚠️ 检测到可能的高风险信号：{'、'.join(reasons)}。不适合线上继续辨证，建议尽快就医评估。"
                return {"veto": True, "message": msg}

        # Default: no veto
        return {"veto": False, "message": ""}