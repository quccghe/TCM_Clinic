from __future__ import annotations
import re
from typing import List

def normalize_question(q: str) -> str:
    t = (q or "").strip().lower()
    t = re.sub(r"\d+(\.\d+)?", "", t)          # 去数字
    t = re.sub(r"[，。！？、,.!?()\[\]{}:：;；\"'“”‘’]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # 同义归一（可继续扩展）
    t = t.replace("是否测量过体温", "体温多少")
    t = t.replace("最高体温多少", "体温多少")
    t = t.replace("有没有发热", "是否发热")
    t = t.replace("有没有寒战", "是否寒战")
    t = t.replace("有没有气促", "是否气促")
    t = t.replace("有没有胸痛", "是否胸痛")
    return t

def jaccard(a: str, b: str) -> float:
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def is_semantic_duplicate(q: str, asked: List[str], threshold: float = 0.75) -> bool:
    nq = normalize_question(q)
    for old in asked:
        no = normalize_question(old)
        if nq == no:
            return True
        if jaccard(nq, no) >= threshold:
            return True
    return False