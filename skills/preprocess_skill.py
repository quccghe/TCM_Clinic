import re
from typing import Dict, Any, List

NEG_PAT = [
    (r"不(胸痛|胸口痛|胸闷)", "no_chest_pain"),
    (r"不(气促|气喘|呼吸困难)", "no_dyspnea"),
    (r"不(口渴|渴)", "no_thirst"),
    (r"不(多尿|尿多|尿频)", "no_polyuria"),
    (r"不(多饮|喝得多)", "no_polydipsia"),
    (r"不(多食|易饥)", "no_polyphagia"),
    (r"无(发热|高热)", "no_fever"),
]

def normalize_text(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"(?m)^\s*\d+\s*[\.、]\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_negations(text: str) -> List[str]:
    t = text or ""
    hits = []
    for pat, tag in NEG_PAT:
        if re.search(pat, t):
            hits.append(tag)
    return hits

def fill_normal_fields(case: Dict[str, Any], text: str) -> None:
    t = (text or "").strip()
    inq = case["four_diagnosis"]["inquiry"]
    if any(k in t for k in ["大小便正常", "二便正常", "大便小便正常"]):
        inq["stool"] = inq.get("stool") or "正常"
        inq["urine"] = inq.get("urine") or "正常"
    if "大便正常" in t:
        inq["stool"] = inq.get("stool") or "正常"
    if "小便正常" in t:
        inq["urine"] = inq.get("urine") or "正常"