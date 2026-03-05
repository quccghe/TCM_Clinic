import json
from typing import Dict, Any, List
from config import MAX_QUESTIONS_PER_TURN
from skills.llm_client import safe_chat
from skills.dialog_schema import SYNDROME_SLOTS
from skills.question_memory import is_semantic_duplicate

ROUTER_SYS = f"""你是“综合征槽位路由器”（不是诊断医生）。
你会得到：
- user_text：用户原话
- slot_status：槽位完成度（slots字典、missing列表、ratio）
- triggered_syndromes：综合征候选
- asked_questions：历史已问问题
- syndrome_defs：各综合征关键问题与关键槽位标签
任务：生成下一轮最多{MAX_QUESTIONS_PER_TURN}个“高信息增益”问题。

硬规则：
- 只问 slot_status.missing 或 综合征critical_slot_tags 对应的缺失信息
- 不要重复问（包括同义问题）
- 若slot_status.ratio已经很高（>=0.75），尽量减少追问，允许空问题列表
只输出JSON：
{{
  "triggered_syndromes": ["..."],
  "next_questions": ["..."],
  "critical_slots_missing": ["slot_tag"...],
  "router_notes": "一句话"
}}
"""

def _rule_trigger(text: str) -> List[str]:
    t = text or ""
    hits = []
    for name, cfg in SYNDROME_SLOTS.items():
        if any(k in t for k in cfg.get("triggers", [])):
            hits.append(name)
    return hits[:3]

def _critical_missing(synds: List[str]) -> List[str]:
    out = []
    for s in synds:
        out.extend(SYNDROME_SLOTS.get(s, {}).get("critical_slot_tags", []))
    return list(dict.fromkeys(out))[:10]

class RouterAgent:
    def run(self, case: Dict[str, Any], user_text: str, slot_status: Dict[str, Any]) -> Dict[str, Any]:
        asked = case.get("asked_questions", [])[-50:]
        rule_hits = _rule_trigger(user_text)

        payload = {
            "user_text": user_text,
            "slot_status": slot_status,
            "triggered_syndromes": rule_hits,
            "asked_questions": asked,
            "syndrome_defs": {
                k: {"critical_questions": v["critical_questions"], "critical_slot_tags": v["critical_slot_tags"]}
                for k, v in SYNDROME_SLOTS.items()
            }
        }

        fallback = json.dumps({
            "triggered_syndromes": rule_hits,
            "next_questions": [],
            "critical_slots_missing": _critical_missing(rule_hits),
            "router_notes": "fallback"
        }, ensure_ascii=False)

        out = safe_chat(
            [{"role":"system","content":ROUTER_SYS},{"role":"user","content":json.dumps(payload, ensure_ascii=False)}],
            fallback=fallback, model_env="OPENAI_MODEL", temperature=0.2
        )

        try:
            data = json.loads(out)
        except Exception:
            data = json.loads(fallback)

        qs = []
        for q in (data.get("next_questions") or []):
            q = (q or "").strip()
            if not q:
                continue
            if is_semantic_duplicate(q, asked):
                continue
            if q not in qs:
                qs.append(q)

        data["next_questions"] = qs[:MAX_QUESTIONS_PER_TURN]
        data["triggered_syndromes"] = data.get("triggered_syndromes") or rule_hits
        data["critical_slots_missing"] = data.get("critical_slots_missing") or _critical_missing(data["triggered_syndromes"])
        return data