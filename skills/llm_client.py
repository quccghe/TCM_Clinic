import os
from typing import List, Dict
from openai import OpenAI

def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "")
    if not api_key or not base_url:
        raise RuntimeError("Missing OPENAI_API_KEY or OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url)

def chat(messages: List[Dict[str, str]], model_env: str, temperature: float = 0.2) -> str:
    model = os.getenv(model_env, "")
    if not model:
        raise RuntimeError(f"Missing model env: {model_env}")
    cli = _client()
    resp = cli.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""

def safe_chat(messages: List[Dict[str, str]], fallback: str, model_env: str, temperature: float = 0.2) -> str:
    try:
        return chat(messages, model_env=model_env, temperature=temperature)
    except Exception:
        return fallback