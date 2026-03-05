from typing import Dict, Any, List

FIELDS = [
    "chief_complaint","present_illness","symptoms",
    "cold_heat","sweat","thirst","appetite",
    "stool","urine","sleep","pain",
    "menses_pregnancy","past_history","allergy",
    "tongue","pulse"
]

def missing_fields(case: Dict[str, Any]) -> List[str]:
    fd = case["four_diagnosis"]
    inq = fd["inquiry"]
    miss = []

    for k in FIELDS:
        if k == "tongue":
            if not str(fd["inspection"].get("tongue","")).strip():
                miss.append("tongue")
            continue
        if k == "pulse":
            if not str(fd["palpation"].get("pulse","")).strip():
                miss.append("pulse")
            continue

        v = inq.get(k, "")
        if isinstance(v, list):
            if len(v) == 0:
                miss.append(k)
        else:
            if not str(v).strip():
                miss.append(k)
    return miss