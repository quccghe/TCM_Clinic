import os
import requests
from typing import Any, Dict

class MCPClient:
    def __init__(self, base_url: str | None = None, timeout: int = 30):
        self.base_url = base_url or os.getenv("MCP_BASE_URL", "http://127.0.0.1:9000")
        self.timeout = timeout

    def call(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + path
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def rag_search(self, query: str, topk: int = 4) -> Dict[str, Any]:
        return self.call("/tools/rag_search", {"query": query, "topk": topk})

    def redflag_check(self, text: str) -> Dict[str, Any]:
        return self.call("/tools/redflag_check", {"text": text})