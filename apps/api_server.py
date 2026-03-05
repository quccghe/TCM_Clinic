# apps/api_server.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any

from config import APP_HOST, APP_PORT
from master_agent import MasterAgent
from skills.case_store_skill import load_case, list_cases
from skills.export_skill import export_case_pdf, export_case_docx

app = FastAPI(title="TCM Clinic Multi-Agent System", version="0.2.0")
master = MasterAgent()

class ChatReq(BaseModel):
    message: str
    case_id: Optional[str] = None
    stage: Optional[Literal["initial","revisit"]] = "initial"

class EvidenceSummaryItem(BaseModel):
    rank: Optional[int] = None
    score: Optional[float] = None
    source: Optional[str] = ""
    snippet: Optional[str] = ""

class ChatResp(BaseModel):
    case_id: str
    message: str
    state: str
    risk: Dict[str, Any]
    evidence_summary: List[EvidenceSummaryItem]
    next_questions: List[str]

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResp)
def chat(req: ChatReq):
    try:
        res = master.chat(req.message, case_id=req.case_id, stage=req.stage or "initial")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/revisit/start", response_model=ChatResp)
def revisit_start(last_case_id: str = Query(..., description="上一次问诊的 case_id")):
    try:
        res = master.start_revisit(last_case_id)
        return res
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="last_case_id not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/case/{case_id}")
def get_case(case_id: str):
    try:
        return load_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="case not found")

@app.get("/cases")
def get_cases():
    return {"cases": list_cases()}

@app.post("/export/{case_id}")
def export(case_id: str, fmt: Literal["pdf","docx"] = "pdf"):
    case = load_case(case_id)
    if fmt == "pdf":
        path = export_case_pdf(case)
    else:
        path = export_case_docx(case)
    return {"ok": True, "path": path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)