import json
from typing import Dict, Any
from skills.llm_client import safe_chat
from skills.preprocess_skill import fill_normal_fields

SCRIBE_SYS = """你是中医问诊记录员。请从用户本轮话中抽取并输出严格JSON：
{
  "chief_complaint": "",
  "present_illness": "",
  "symptoms_add": [],
  "cold_heat": "",
  "sweat": "",
  "thirst": "",
  "appetite": "",
  "stool": "",
  "urine": "",
  "sleep": "",
  "pain": "",
  "tongue": "",
  "pulse": "",
  "past_history": "",
  "allergy": ""
}
没提到填空字符串或空数组。只输出JSON。"""

class ScribeAgent:
    def run(self, case: Dict[str, Any], user_text: str) -> None:
        fill_normal_fields(case, user_text)

        fallback = json.dumps({
            "chief_complaint": "",
            "present_illness": "",
            "symptoms_add": [],
            "cold_heat": "",
            "sweat": "",
            "thirst": "",
            "appetite": "",
            "stool": case["four_diagnosis"]["inquiry"].get("stool",""),
            "urine": case["four_diagnosis"]["inquiry"].get("urine",""),
            "sleep": "",
            "pain": "",
            "tongue": "",
            "pulse": "",
            "past_history": "",
            "allergy": "",
        }, ensure_ascii=False)

        out = safe_chat(
            [{"role":"system","content":SCRIBE_SYS},{"role":"user","content":user_text}],
            fallback=fallback,
            model_env="SCRIBE_MODEL",
            temperature=0.1
        )
        try:
            data = json.loads(out)
        except Exception:
            data = json.loads(fallback)

        fd = case["four_diagnosis"]
        inq = fd["inquiry"]

        def put(k):
            v = data.get(k, "")
            if isinstance(v, str) and v.strip():
                inq[k] = v.strip()

        for k in ["chief_complaint","present_illness","cold_heat","sweat","thirst","appetite","stool","urine","sleep","pain","past_history","allergy"]:
            put(k)

        if isinstance(data.get("symptoms_add"), list) and data["symptoms_add"]:
            merged = list(dict.fromkeys((inq.get("symptoms",[]) or []) + data["symptoms_add"]))
            inq["symptoms"] = merged

        tongue = (data.get("tongue") or "").strip()
        pulse = (data.get("pulse") or "").strip()
        if tongue:
            fd["inspection"]["tongue"] = tongue
        if pulse:
            fd["palpation"]["pulse"] = pulse