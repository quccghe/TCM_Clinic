import re
from typing import Dict, Any, List
from .rag_tools import rag_search

# --- 简易病名规则：可继续扩展 ---
# 目的：先把“只出证型不出病名”这个核心缺陷补上。
def _rule_disease_candidates(text: str) -> List[Dict[str, Any]]:
    t = text or ""
    cands = []

    # 消渴：三多一少/口渴多饮/多尿/多食易饥/消瘦/尿黄量多
    if any(k in t for k in ["口渴", "喝多少水都不解渴", "多饮", "总想喝水"]) and any(k in t for k in ["尿多", "多尿", "总想上厕所", "尿量多"]):
        score = 0.88
        subtype = "未定"
        if any(k in t for k in ["上消", "肺", "咽干", "口干舌燥"]):
            subtype = "上消"
        if any(k in t for k in ["易饥", "多食", "胃口特别大", "饿得快"]):
            subtype = "中消"
        if any(k in t for k in ["尿黄", "尿频", "腰膝酸软", "耳鸣"]):
            subtype = "下消"
        cands.append({"name": "消渴", "score": score, "subtype": subtype, "basis": "口渴多饮+小便频多（并可伴易饥/消瘦）"})

    # 不寐
    if any(k in t for k in ["失眠", "睡不着", "入睡困难", "多梦", "早醒"]):
        cands.append({"name": "不寐", "score": 0.75, "subtype": "未定", "basis": "睡眠障碍相关描述"})

    # 泄泻/腹痛（示例）
    if any(k in t for k in ["腹泻", "拉肚子", "便溏"]):
        cands.append({"name": "泄泻", "score": 0.70, "subtype": "未定", "basis": "大便稀溏/腹泻"})

    cands.sort(key=lambda x: x["score"], reverse=True)
    return cands[:5]

def disease_rank(text: str) -> Dict[str, Any]:
    cands = _rule_disease_candidates(text)

    # 再用 RAG 拉 2-3 条“病名要点”作为可解释依据
    q = (cands[0]["name"] if cands else "中医 病名 证型 鉴别") + " 鉴别 要点"
    ev = rag_search(q, topk=3).get("results", [])

    final = cands[0]["name"] if cands else ""
    subtype = cands[0]["subtype"] if cands else "未定"
    return {"ok": True, "final": final, "subtype": subtype, "candidates": cands, "evidence": ev}

# 术语规范化：把口语“红红的、苔不多、有点干”→“舌红少苔偏干”等
def tcm_term_normalize(text: str) -> Dict[str, Any]:
    t = text or ""
    out = {"ok": True, "tongue": "", "pulse": "", "other": ""}

    # 舌象简单规则
    if "舌" in t:
        tongue = []
        if any(k in t for k in ["舌红", "红红的", "偏红"]): tongue.append("舌红")
        if any(k in t for k in ["苔少", "苔不多", "少苔"]): tongue.append("少苔")
        if any(k in t for k in ["黄", "偏黄"]): tongue.append("苔偏黄")
        if any(k in t for k in ["干", "干干的", "少津"]): tongue.append("少津偏干")
        if tongue:
            out["tongue"] = "，".join(tongue)

    # 脉象简单规则
    if any(k in t for k in ["脉", "手腕跳"]):
        pulse = []
        if any(k in t for k in ["跳得快", "偏快"]): pulse.append("数")
        if any(k in t for k in ["有力", "挺有力"]): pulse.append("有力")
        if any(k in t for k in ["细", "细细的"]): pulse.append("细")
        if any(k in t for k in ["紧", "绷紧"]): pulse.append("弦/紧")
        if pulse:
            out["pulse"] = "、".join(pulse)
    return out

def disease_method_formula_lookup(disease: str, syndrome: str) -> Dict[str, Any]:
    q = f"{disease} {syndrome} 治法 方"
    ev = rag_search(q, topk=4).get("results", [])
    # 轻量结构化：从证据中抽“治法/方名”不强求100%命中，命中则填
    method = ""
    formulas = []
    for e in ev:
        tx = e.get("text","")
        if not method and any(k in tx for k in ["治法", "治则", "治宜", "当以"]):
            method = tx.replace("\n"," ")[:120]
        # 粗抓常见“XX汤/XX散/XX丸”
        formulas += re.findall(r"[\u4e00-\u9fa5]{2,8}(汤|散|丸|饮)", tx)
    formulas = list(dict.fromkeys(formulas))[:6]
    return {"ok": True, "disease": disease, "syndrome": syndrome, "method": method or "以辨证为准（方向性治法，需线下医师确认）", "formulas": formulas, "evidence": ev}

def dietary_plan_lookup(disease: str, syndrome: str) -> Dict[str, Any]:
    q = f"{disease} {syndrome} 饮食 宜忌 食疗"
    ev = rag_search(q, topk=4).get("results", [])
    # 简单输出结构（可继续扩展）
    # 消渴（阴虚燥热）一般倾向：清淡、少糖、少辛辣、避免酒、避免甜腻；多蔬菜粗粮，适量蛋白
    suggest = []
    avoid = []
    if "消渴" in disease:
        suggest = ["清淡饮食", "多蔬菜粗粮", "适量优质蛋白", "少量多餐", "足量饮水（视情况）"]
        avoid = ["高糖甜饮", "辛辣烧烤", "酒精", "油腻甜腻", "熬夜"]
    return {"ok": True, "disease": disease, "syndrome": syndrome, "suggest": suggest, "avoid": avoid, "evidence": ev}