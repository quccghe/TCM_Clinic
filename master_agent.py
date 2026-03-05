from __future__ import annotations
from typing import Dict, Any, Optional, List

from config import MAX_TURNS, MAX_CONSECUTIVE_DECLINES, DIAG_CONF_THRESHOLD, MAX_QUESTIONS_PER_TURN, SLOT_DIAG_TRIGGER
from skills.case_store_skill import new_case, load_case, save_case, append_turn
from skills.preprocess_skill import normalize_text, fill_normal_fields, extract_negations
from skills.refusal_skill import is_decline
from skills.mcp_client import MCPClient
from skills.confidence_calibrator import calibrate_confidence
from skills.slot_manager import compute_slot_status
from skills.question_memory import is_semantic_duplicate

from agents.safety_agent import SafetyAgent
from agents.scribe_agent import ScribeAgent
from agents.router_agent import RouterAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.advice_agent import AdviceAgent


class MasterAgent:
    def __init__(self):
        self.mcp = MCPClient()
        self.safety = SafetyAgent()
        self.scribe = ScribeAgent()
        self.router = RouterAgent()
        self.diag = DiagnosisAgent()
        self.advice_agent = AdviceAgent()

    def chat(self, message: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        if not case_id:
            case_id = new_case()
        case = load_case(case_id)

        if case.get("turn_count_user", 0) >= MAX_TURNS:
            msg = "本次问诊轮次已达到上限。建议整理信息并线下面诊进一步评估。"
            append_turn(case, "assistant", msg)
            case["state"] = "CLOSED"
            save_case(case)
            return self._resp(case, msg)

        user_text = normalize_text(message)
        append_turn(case, "user", user_text)
        case["turn_count_user"] += 1

        # decline
        if is_decline(user_text):
            case["consecutive_declines"] += 1
        else:
            case["consecutive_declines"] = 0

        # negations
        negs = extract_negations(user_text)
        if negs:
            case["negations"] = list(dict.fromkeys((case.get("negations", []) or []) + negs))

        # safety
        sv = self.safety.run(case, user_text, recent_dialog=case.get("turns", [])[-6:])
        if sv.get("veto"):
            msg = sv["message"]
            append_turn(case, "assistant", msg)
            case["state"] = "CLOSED"
            save_case(case)
            return self._resp(case, msg)

        # preprocess + scribe
        fill_normal_fields(case, user_text)
        self.scribe.run(case, user_text)

        # slot status (核心)
        slot_status = compute_slot_status(case)
        case["slot_status"] = slot_status

        # router asks only missing
        router_out = self.router.run(case, user_text, slot_status=slot_status)
        case["router"]["syndromes"] = router_out.get("triggered_syndromes", [])
        case["router"]["critical_slots_missing"] = router_out.get("critical_slots_missing", [])

        # RAG
        diag_query = self._build_rag_query(case, user_text)
        rag = self.mcp.rag_search(query=diag_query, topk=4)
        ev4 = rag.get("results", []) if rag.get("ok") else []
        case["evidence"] = ev4

        # diagnosis payload includes slot_status
        tool_payload = {
            "recent_dialog": case.get("turns", [])[-14:],
            "four_diagnosis": case.get("four_diagnosis", {}),
            "negations": case.get("negations", []),
            "router": case.get("router", {}),
            "slot_status": slot_status,
            "evidence": [{"idx": i+1, **e} for i, e in enumerate(ev4)],
            "asked_questions": case.get("asked_questions", [])[-50:],
        }
        diag_out = self.diag.run(tool_payload)

        # merge questions (router first) + semantic dedup
        asked = case.get("asked_questions", [])
        next_qs = []
        for q in (router_out.get("next_questions", []) or []) + (diag_out.get("questions", []) or []):
            q = (q or "").strip()
            if not q:
                continue
            if is_semantic_duplicate(q, asked):
                continue
            if q not in next_qs:
                next_qs.append(q)
        next_qs = next_qs[:MAX_QUESTIONS_PER_TURN]

        # If slot completion already high -> allow diagnosis even if model hesitates
        slot_ratio = float(slot_status.get("ratio", 0.0) or 0.0)
        force_try_diagnose = slot_ratio >= SLOT_DIAG_TRIGGER and not (diag_out.get("contradictions") or [])

        critical_missing = list(dict.fromkeys(case["router"].get("critical_slots_missing", []) + (diag_out.get("critical_slots_missing") or [])))
        diag_out["critical_slots_missing"] = critical_missing

        # 如果关键槽位缺失且还有问题可问 -> 问
        if critical_missing and next_qs:
            diag_out["action"] = "ask"

        if diag_out.get("action") == "ask" and not force_try_diagnose:
            if case["consecutive_declines"] >= MAX_CONSECUTIVE_DECLINES:
                msg = "信息不足以形成高置信度判断。建议线下面诊进一步辨证；如症状加重请及时就医。"
                append_turn(case, "assistant", msg)
                case["state"] = "CLOSED"
                save_case(case)
                return self._resp(case, msg)

            for q in next_qs:
                case["asked_questions"].append(q)

            # 如果没问题了，就不要空问（直接进入诊断尝试）
            if not next_qs:
                force_try_diagnose = True
            else:
                msg = "为了更准确判断，请你回答：\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(next_qs)])
                append_turn(case, "assistant", msg)
                save_case(case)
                return self._resp(case, msg, next_questions=next_qs)

        # ---- Diagnose path ----
        raw_conf = float(diag_out.get("raw_confidence", 0.0) or 0.0)
        cal = calibrate_confidence(
            raw_conf=raw_conf,
            evidence_strength=float(diag_out.get("evidence_strength", 0.0) or 0.0),
            chief_match=float(diag_out.get("chief_match_score", 0.0) or 0.0),
            exclusion_gap=float(diag_out.get("exclusion_gap", 0.0) or 0.0),
            risk_cap=float(diag_out.get("risk_cap", 0.0) or 0.0),
            critical_slots_missing=critical_missing if not force_try_diagnose else [],
        )
        calibrated_conf = cal["calibrated_conf"]

        case["decision"] = {
            "disease": (diag_out.get("disease") or "").strip(),
            "subtype": (diag_out.get("subtype") or "").strip(),
            "syndrome": (diag_out.get("syndrome") or "").strip(),
            "organs": diag_out.get("organs") or [],
            "mechanism_chain": diag_out.get("mechanism_chain") or [],
            "key_symptoms": diag_out.get("key_symptoms") or [],
            "brief_basis": (diag_out.get("brief_basis") or "").strip(),
            "raw_conf": raw_conf,
            "calibrated_conf": calibrated_conf,
            "conf_parts": {"slot_ratio": slot_ratio, **cal.get("parts", {}), "cap_reason": cal.get("cap_reason")},
            "critical_slots_missing": critical_missing,
        }

        # 置信度不足且还有可问问题 -> 问；否则给“倾向性结论”
        if calibrated_conf < DIAG_CONF_THRESHOLD and next_qs:
            for q in next_qs:
                case["asked_questions"].append(q)
            msg = "为了更准确判断，请你回答：\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(next_qs)])
            append_turn(case, "assistant", msg)
            save_case(case)
            return self._resp(case, msg, next_questions=next_qs)

        # Advice RAG
        q2 = f"{case['decision']['disease']} {case['decision']['syndrome']} 治法 调护 宜忌"
        rag2 = self.mcp.rag_search(query=q2[:220], topk=4)
        advice_ev = rag2.get("results", []) if rag2.get("ok") else []
        advice = self.advice_agent.run(case["decision"], advice_ev)
        case["advice"] = advice
        case["state"] = "CLOSED"

        msg = (
            f"【初步判断（槽位完成度 {slot_ratio:.2f}；校准置信度 {calibrated_conf:.2f}）】\n"
            f"病名：{case['decision']['disease'] or '—'} {('（'+case['decision']['subtype']+'）') if case['decision']['subtype'] else ''}\n"
            f"证型：{case['decision']['syndrome'] or '—'}\n"
            f"病位：{'、'.join(case['decision']['organs']) if case['decision']['organs'] else '—'}\n"
            f"病机链：{'；'.join(case['decision']['mechanism_chain']) if case['decision']['mechanism_chain'] else '—'}\n"
            f"主症：{'、'.join(case['decision']['key_symptoms']) if case['decision']['key_symptoms'] else '—'}\n"
            f"依据：{case['decision']['brief_basis'] or '—'}\n\n"
            f"【建议】\n{advice}"
        )
        append_turn(case, "assistant", msg)
        save_case(case)
        return self._resp(case, msg)

    def _build_rag_query(self, case: Dict[str, Any], user_text: str) -> str:
        fd = case.get("four_diagnosis", {})
        inq = (fd.get("inquiry") or {})
        tongue = (fd.get("inspection") or {}).get("tongue","")
        pulse = (fd.get("palpation") or {}).get("pulse","")
        synds = case.get("router", {}).get("syndromes", []) or []
        parts = [user_text]
        for k in ["chief_complaint","present_illness","thirst","appetite","stool","urine","sleep","pain","cold_heat","sweat"]:
            v = (inq.get(k) or "").strip()
            if v:
                parts.append(v)
        if tongue: parts.append(tongue)
        if pulse: parts.append(pulse)
        if synds: parts.append("综合征:" + ",".join(synds))
        return " ".join(parts)[:240]

    def _resp(self, case: Dict[str, Any], message: str, next_questions: Optional[List[str]] = None) -> Dict[str, Any]:
        summary = []
        for i, e in enumerate((case.get("evidence") or [])[:4], start=1):
            txt = (e.get("text") or "").replace("\n", " ")
            summary.append({"idx": i, "score": e.get("score"), "source": e.get("source",""), "snippet": txt[:160]})
        return {
            "case_id": case["case_id"],
            "state": case.get("state",""),
            "message": message,
            "next_questions": next_questions or [],
            "slot_status": case.get("slot_status", {}),
            "router": case.get("router", {}),
            "decision": case.get("decision", {}),
            "evidence_summary": summary,
            "risk": case.get("risk", {}),
        }