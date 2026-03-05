import os, json
from typing import Any, Dict, List
import numpy as np
import hnswlib
from sentence_transformers import SentenceTransformer
from config import RAG_VEC_DIR

_RETRIEVER = None

class HNSWRetriever:
    def __init__(self, vec_dir: str):
        meta_path = os.path.join(vec_dir, "index_meta.json")
        chunks_path = os.path.join(vec_dir, "chunks_vec.jsonl")
        index_path = os.path.join(vec_dir, "hnsw_index.bin")

        if not (os.path.exists(meta_path) and os.path.exists(chunks_path) and os.path.exists(index_path)):
            raise FileNotFoundError(f"RAG files not found in: {vec_dir}")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.model_name = meta.get("model", "BAAI/bge-small-zh-v1.5")
        self.dim = int(meta.get("dim", 384))
        self.space = meta.get("metric", "cosine")

        self.model = SentenceTransformer(self.model_name)

        self.index = hnswlib.Index(space=self.space, dim=self.dim)
        self.index.load_index(index_path)
        self.index.set_ef(64)

        self.chunks = []
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.chunks.append(json.loads(line))

    def query(self, q: str, topk: int) -> List[Dict[str, Any]]:
        emb = self.model.encode([q], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
        labels, dists = self.index.knn_query(emb, k=topk)
        labels = labels[0]
        dists = dists[0]
        res = []
        for rank, (idx, dist) in enumerate(zip(labels, dists), start=1):
            idx = int(idx)
            score = float(1.0 - dist)
            ch = self.chunks[idx]
            meta = ch.get("meta", {}) or ch.get("metadata", {}) or {}
            res.append({
                "rank": rank,
                "score": score,
                "source": meta.get("source") or meta.get("source_file") or meta.get("file") or "unknown",
                "chunk_id": meta.get("chunk_id") or idx,
                "text": ch.get("text", "")
            })
        return res

def _get() -> HNSWRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = HNSWRetriever(RAG_VEC_DIR)
    return _RETRIEVER

def rag_search(query: str, topk: int = 4) -> Dict[str, Any]:
    try:
        hits = _get().query(query, topk=topk)
        return {"ok": True, "results": hits}
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}