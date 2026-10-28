"""Minimal client for a local Ollama server."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class LLMUnavailable(RuntimeError):
    pass


def _host() -> str:
    return os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def model_name() -> str:
    return os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


def _request(path: str, payload: dict | None = None, timeout: float = 120) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        _host() + path, data=data, headers={"Content-Type": "application/json"}, method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise LLMUnavailable(str(exc)) from exc


def status() -> dict:
    try:
        tags = _request("/api/tags", timeout=3)
    except LLMUnavailable as exc:
        return {"available": False, "model": model_name(), "models": [], "error": str(exc)}
    models = [m.get("name") for m in tags.get("models", [])]
    return {"available": True, "model": model_name(), "models": models, "model_installed": model_name() in models}


def chat(messages: list[dict]) -> str:
    reply = _request(
        "/api/chat",
        {"model": model_name(), "messages": messages, "stream": False, "options": {"temperature": 0.1}},
    )
    return (reply.get("message") or {}).get("content", "").strip()
