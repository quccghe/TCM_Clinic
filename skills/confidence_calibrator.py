from typing import Dict, Any, List

def calibrate_confidence(
    raw_conf: float,
    evidence_strength: float,
    chief_match: float,
    exclusion_gap: float,
    risk_cap: float,
    critical_slots_missing: List[str],
) -> Dict[str, Any]:
    E = max(0.0, min(1.0, evidence_strength))
    C = max(0.0, min(1.0, chief_match))
    X = max(0.0, min(1.0, exclusion_gap))
    R = max(0.0, min(1.0, risk_cap))

    final_conf = 0.35 * E + 0.35 * C + 0.20 * X + 0.10 * R

    cap_reason = None
    if critical_slots_missing:
        final_conf = min(final_conf, 0.75)
        cap_reason = "critical_slots_missing_cap_0.75"

    final_conf = min(final_conf, max(0.0, raw_conf))

    return {
        "calibrated_conf": float(final_conf),
        "parts": {"E": E, "C": C, "X": X, "R": R},
        "cap_reason": cap_reason,
    }