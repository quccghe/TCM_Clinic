# agents/evidence_agent.py
from typing import Dict, Any, List
from skills.mcp_client import MCPClient


class EvidenceAgent:
    """
    通过 MCP 调用 rag_search，从你的 HNSW 向量库中检索证据。
    master_agent.py 会 import EvidenceAgent，所以名字必须严格叫 EvidenceAgent。
    """

    def __init__(self):
        self.mcp = MCPClient()

    def run(self, case: Dict[str, Any], topk: int = 5) -> Dict[str, Any]:
        inq = case["four_diagnosis"]["inquiry"]
        tongue = case["four_diagnosis"]["inspection"].get("tongue", "")
        pulse = case["four_diagnosis"]["palpation"].get("pulse", "")
        syms = inq.get("symptoms", []) or []
        cold_heat = inq.get("cold_heat", "") or ""
        sleep = inq.get("sleep", "") or ""

        query_parts: List[str] = []
        query_parts.extend([s for s in syms if isinstance(s, str) and s.strip()])
        for x in [tongue, pulse, cold_heat, sleep]:
            if isinstance(x, str) and x.strip():
                query_parts.append(x.strip())

        query = " ".join(query_parts).strip() or "中医 问诊 证型"
        res = self.mcp.rag_search(query=query, topk=topk)

        if res.get("ok"):
            case["evidence"] = res.get("results", []) or []
        else:
            case["evidence"] = []

        return {"ok": True, "query": query, "evidence": case["evidence"]}