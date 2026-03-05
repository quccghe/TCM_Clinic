import os
import math
import re
from typing import List, Dict, Any, Tuple
from config import RAG_SOURCE_FILE

def _read_source(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _chunk_text(text: str, max_chars: int = 800) -> List[str]:
    # 按空行分段，再合并到 max_chars 左右
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = buf + ("\n\n" if buf else "") + p
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks

def _tokenize(s: str) -> List[str]:
    s = s.lower()
    # 简单中文/英文 token：中文按2-3gram+关键词效果会好些，这里先用“汉字/字母数字连续串”
    tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9]+", s)
    # 再把长中文串切成2-gram，提升召回
    out = []
    for t in tokens:
        if re.fullmatch(r"[\u4e00-\u9fff]+", t) and len(t) >= 3:
            for i in range(len(t) - 1):
                out.append(t[i:i+2])
            out.append(t)  # 原串也保留
        else:
            out.append(t)
    return out

def _tf(tokens: List[str]) -> Dict[str, float]:
    d = {}
    for t in tokens:
        d[t] = d.get(t, 0.0) + 1.0
    n = max(1.0, float(len(tokens)))
    for k in list(d.keys()):
        d[k] /= n
    return d

def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    # sparse cosine
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

class SimpleRAG:
    def __init__(self, source_path: str = RAG_SOURCE_FILE):
        self.source_path = source_path
        self.chunks: List[str] = []
        self.chunk_vecs: List[Dict[str, float]] = []

    def build(self) -> None:
        text = _read_source(self.source_path)
        self.chunks = _chunk_text(text)
        self.chunk_vecs = [_tf(_tokenize(c)) for c in self.chunks]

    def search(self, query: str, topk: int = 4) -> List[Dict[str, Any]]:
        if not self.chunks:
            self.build()
        qv = _tf(_tokenize(query))
        scored: List[Tuple[float, int]] = []
        for i, cv in enumerate(self.chunk_vecs):
            s = _cosine(qv, cv)
            scored.append((s, i))
        scored.sort(reverse=True)
        out = []
        for score, idx in scored[:topk]:
            out.append({
                "chunk_id": idx,
                "score": round(float(score), 4),
                "text": self.chunks[idx]
            })
        return out