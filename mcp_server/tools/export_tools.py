import os
from skills.case_store_skill import load_case
from skills.export_skill import export_case_pdf, export_case_docx

def export_pdf(case_id: str):
    case = load_case(case_id)
    path = export_case_pdf(case)
    return {"ok": True, "path": os.path.abspath(path)}

def export_docx(case_id: str):
    case = load_case(case_id)
    path = export_case_docx(case)
    return {"ok": True, "path": os.path.abspath(path)}