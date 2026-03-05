from skills.case_store_skill import load_case

def case_load(case_id: str):
    try:
        return {"ok": True, "case": load_case(case_id)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def case_diff(case_id_a: str, case_id_b: str):
    a = load_case(case_id_a)
    b = load_case(case_id_b)
    # 简单diff：症状/舌/脉/睡眠/二便
    def pick(c):
        fd = c["four_diagnosis"]
        inq = fd["inquiry"]
        return {
            "symptoms": inq.get("symptoms", []),
            "tongue": fd["inspection"].get("tongue",""),
            "pulse": fd["palpation"].get("pulse",""),
            "sleep": inq.get("sleep",""),
            "stool": inq.get("stool",""),
            "urine": inq.get("urine",""),
        }
    pa, pb = pick(a), pick(b)
    return {"ok": True, "a": pa, "b": pb}