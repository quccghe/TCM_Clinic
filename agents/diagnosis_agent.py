import json
from typing import Dict, Any
from skills.llm_client import safe_chat
from config import DIAG_CONF_THRESHOLD

DIAG_SYS = """你是中医问诊与鉴别诊断医生（通用，不限病种）。
输入包含：对话、结构化四诊、RAG证据、槽位完成度slot_status、综合征信息router。
请输出严格JSON：
{
  "action": "ask" 或 "diagnose",
  "questions": [],
  "disease": "",
  "subtype": "",
  "syndrome": "",
  "organs": [],
  "mechanism_chain": [],
  "key_symptoms": [],
  "brief_basis": "",
  "raw_confidence": 0~1,
  "chief_match_score": 0~1,
  "exclusion_gap": 0~1,
  "evidence_strength": 0~1,
  "risk_cap": 0~1,
  "critical_slots_missing": [],
  "contradictions": []
}

规则：
- 若slot_status.ratio >= 0.70 且 无明显contradictions，则允许action=diagnose（即便raw_conf略低，也请尽量给出“倾向性判断”）
- 若关键槽位确实缺失（critical_slots_missing非空），优先ask
- 不要重复问已回答内容
只输出JSON。
"""

def _fallback():
    return {
        "action":"ask","questions":["请补充：你最困扰的主症是什么？持续多久？是否发热/咳嗽/二便异常？"],
        "disease":"","subtype":"","syndrome":"","organs":[],
        "mechanism_chain":[],"key_symptoms":[],"brief_basis":"",
        "raw_confidence":0.3,"chief_match_score":0.3,"exclusion_gap":0.2,"evidence_strength":0.2,"risk_cap":0.2,
        "critical_slots_missing":[],"contradictions":[]
    }

class DiagnosisAgent:
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fb = json.dumps(_fallback(), ensure_ascii=False)
        out = safe_chat(
            [{"role":"system","content":DIAG_SYS},{"role":"user","content":json.dumps(payload, ensure_ascii=False)}],
            fallback=fb, model_env="OPENAI_MODEL", temperature=0.2
        )
        try:
            data = json.loads(out)
        except Exception:
            data = _fallback()
        return data