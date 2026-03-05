from __future__ import annotations
from typing import Dict, Any, Tuple, List

def _contains_any(text: str, keys: List[str]) -> bool:
    t = (text or "")
    return any(k in t for k in keys)

def compute_slot_status(case: Dict[str, Any]) -> Dict[str, Any]:
    fd = case.get("four_diagnosis", {})
    inq = (fd.get("inquiry") or {})
    insp = (fd.get("inspection") or {})
    palp = (fd.get("palpation") or {})

    symptoms = " ".join(inq.get("symptoms") or [])
    present = (inq.get("present_illness") or "")
    cc = (inq.get("chief_complaint") or "")

    # 通用槽位（对大多数内科问诊有效）
    slots = {
        "onset_duration": bool(cc or present),
        "fever": _contains_any(symptoms + present, ["发热", "高热", "身上发烫", "烧"]) or bool(inq.get("cold_heat")),
        "temp_level": _contains_any(present + cc + symptoms, ["38", "39", "体温", "℃"]),
        "chills": _contains_any(symptoms + present, ["寒战", "打寒战", "发冷", "畏寒"]),
        "sweat_after_fever": _contains_any(symptoms + present, ["出汗", "汗出", "衣服湿"]),
        "cough": _contains_any(symptoms + present, ["咳", "咳嗽"]),
        "phlegm_type": _contains_any(symptoms + present, ["白稀痰", "黄稠痰", "痰", "无痰", "带血"]),
        "dyspnea": _contains_any(symptoms + present, ["气促", "气喘", "呼吸困难", "喘"]),
        "chest_pain": _contains_any(symptoms + present, ["胸痛", "胸口痛", "胸闷"]),
        "urine": bool(inq.get("urine")) or _contains_any(symptoms + present, ["尿黄", "茶色尿", "尿少", "尿量少"]),
        "stool": bool(inq.get("stool")) or _contains_any(symptoms + present, ["便秘", "腹泻", "稀便", "黑便", "便血"]),
        "thirst": bool(inq.get("thirst")) or _contains_any(symptoms + present, ["口干", "口渴"]),
        "appetite": bool(inq.get("appetite")) or _contains_any(symptoms + present, ["纳差", "厌油", "食欲差", "胃口差"]),
        "tongue": bool(insp.get("tongue")),
        "pulse": bool(palp.get("pulse")),
    }

    filled = sum(1 for v in slots.values() if v)
    total = len(slots)
    ratio = filled / total if total else 0.0

    missing = [k for k, v in slots.items() if not v]

    return {
        "slots": slots,
        "filled": filled,
        "total": total,
        "ratio": ratio,
        "missing": missing,
    }