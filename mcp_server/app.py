from fastapi import FastAPI
from pydantic import BaseModel
from .tools.rag_tools import rag_search
from .tools.safety_tools import redflag_check

app = FastAPI(title="TCM MCP Server", version="3.0")

class RagReq(BaseModel):
    query: str
    topk: int = 4

class TextReq(BaseModel):
    text: str

@app.post("/tools/rag_search")
def api_rag(req: RagReq):
    return rag_search(req.query, req.topk)

@app.post("/tools/redflag_check")
def api_redflag(req: TextReq):
    return redflag_check(req.text)