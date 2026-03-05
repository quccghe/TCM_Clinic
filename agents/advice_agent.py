import json
from typing import Dict, Any
from skills.llm_client import safe_chat

ADVICE_SYS = """你是中医问诊建议助手（通用）。
输入：病名+证型+病机链+主症+RAG证据(top4)。
输出要求（自然语言）：
1) 治法方向（1~2句，标本主次清晰：先标实再谈本虚，除非证据充分）
2) 生活方式与作息
3) 饮食宜忌（不要空泛，尽量与证型绑定）
4) 复诊节点/何时就医（尤其出现黄疸加重、发热寒战、剧痛等）
不提供剂量处方；可提“常见方名方向”，并强调需线下辨证确认。
"""

class AdviceAgent:
    def run(self, decision: Dict[str, Any], advice_evidence: list) -> str:
        payload = {
            "decision": decision,
            "evidence": advice_evidence,
        }
        fallback = "信息不足以给出可靠建议。建议线下面诊进一步辨证评估；若出现症状加重或红旗信号请及时就医。"
        out = safe_chat(
            [{"role":"system","content":ADVICE_SYS},{"role":"user","content":json.dumps(payload, ensure_ascii=False)}],
            fallback=fallback,
            model_env="OPENAI_MODEL",
            temperature=0.3
        )
        return out.strip()