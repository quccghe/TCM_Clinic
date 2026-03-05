import re
from typing import Dict, Any, List

_TONGUE_PATTERNS = [
    (r"(舌红|舌质红)", "舌红"),
    (r"(舌淡|舌质淡)", "舌淡"),
    (r"(苔薄白|苔白薄|薄白苔)", "苔薄白"),
    (r"(苔黄|黄苔)", "苔黄"),
    (r"(少苔|苔少)", "少苔"),
    (r"(厚苔|苔厚)", "苔厚"),
]

_PULSE_PATTERNS = [
    (r"(脉细|细脉)", "脉细"),
    (r"(脉数|数脉)", "脉数"),
    (r"(脉弦|弦脉)", "脉弦"),
    (r"(脉滑|滑脉)", "脉滑"),
    (r"(脉沉|沉脉)", "脉沉"),
]

def extract_tongue(text: str) -> str:
    hits = []
    for pat, norm in _TONGUE_PATTERNS:
        if re.search(pat, text):
            hits.append(norm)
    return "，".join(dict.fromkeys(hits))

def extract_pulse(text: str) -> str:
    hits = []
    for pat, norm in _PULSE_PATTERNS:
        if re.search(pat, text):
            hits.append(norm)
    return "，".join(dict.fromkeys(hits))

def extract_symptoms(text: str) -> List[str]:
    # 非穷尽示例：可继续扩充词表/正则
    candidates = [
        "咳嗽","发热","恶寒","鼻塞","流涕","咽痛",
        "失眠","多梦","心悸","健忘","乏力","口渴",
        "腹痛","腹泻","便秘","尿黄","尿频","头痛",
        "胸闷","气短","出汗","盗汗","口苦","口干",
        "焦虑","抑郁","食欲差","反酸","嗳气"
    ]
    found = []
    for w in candidates:
        if w in text:
            found.append(w)
    return list(dict.fromkeys(found))

def update_four_diagnosis(case: Dict[str, Any], user_text: str) -> None:
    fd = case["four_diagnosis"]
    tongue = extract_tongue(user_text)
    pulse = extract_pulse(user_text)
    syms = extract_symptoms(user_text)

    if tongue:
        fd["inspection"]["tongue"] = tongue
        fd["inquiry"]["tongue"] = tongue
    if pulse:
        fd["palpation"]["pulse"] = pulse
        fd["inquiry"]["pulse"] = pulse

    if syms:
        existing = fd["inquiry"].get("symptoms", [])
        merged = list(dict.fromkeys(existing + syms))
        fd["inquiry"]["symptoms"] = merged