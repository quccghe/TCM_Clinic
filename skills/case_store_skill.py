import os, json, time, uuid
from typing import Any, Dict, Optional
from config import CASES_DIR

def _ensure():
    os.makedirs(CASES_DIR, exist_ok=True)

def case_path(case_id: str) -> str:
    return os.path.join(CASES_DIR, f"{case_id}.json")

def new_case(stage: str = "initial", prev_case_id: Optional[str] = None) -> str:
    _ensure()
    case_id = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    now = int(time.time())
    case: Dict[str, Any] = {
        "case_id": case_id,
        "stage": stage,
        "prev_case_id": prev_case_id,
        "state": "COLLECT",
        "created_at": now,
        "updated_at": now,

        "turn_count_user": 0,
        "turn_count_assistant": 0,
        "consecutive_declines": 0,
        "asked_questions": [],
        "negations": [],
        "slot_status": {},
        "router": {"syndromes": [], "critical_slots_missing": []},

        "turns": [],

        "four_diagnosis": {
            "inspection": {"tongue": ""},
            "inquiry": {
                "chief_complaint": "",
                "present_illness": "",
                "symptoms": [],
                "cold_heat": "",
                "sweat": "",
                "thirst": "",
                "appetite": "",
                "stool": "",
                "urine": "",
                "sleep": "",
                "pain": "",
                "menses_pregnancy": "",
                "past_history": "",
                "allergy": "",
            },
            "palpation": {"pulse": ""},
        },

        "evidence": [],

        "decision": {
            "disease": "",
            "subtype": "",
            "syndrome": "",
            "organs": [],
            "mechanism_chain": [],
            "key_symptoms": [],
            "brief_basis": "",
            "raw_conf": 0.0,
            "calibrated_conf": 0.0,
            "conf_parts": {},
            "critical_slots_missing": [],
        },

        "advice": "",
        "risk": {"level": "none", "reasons": []},
    }
    save_case(case)
    return case_id

def load_case(case_id: str) -> Dict[str, Any]:
    _ensure()
    with open(case_path(case_id), "r", encoding="utf-8") as f:
        return json.load(f)

def save_case(case: Dict[str, Any]) -> None:
    _ensure()
    case["updated_at"] = int(time.time())
    with open(case_path(case["case_id"]), "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)

def append_turn(case: Dict[str, Any], role: str, text: str) -> None:
    case["turns"].append({"role": role, "text": text, "ts": int(time.time())})