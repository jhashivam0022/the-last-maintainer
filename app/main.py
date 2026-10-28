"""FastAPI entry point. Run with: uvicorn app.main:app --reload"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import analyzer, investigate, llm, report
from .scanner import resolve_repo

app = FastAPI(title="The Last Maintainer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_cache: dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    path: str


class AskRequest(BaseModel):
    path: str
    question: str


class ReportRequest(BaseModel):
    path: str
    qa: Optional[list[dict]] = None


def _get_analysis(path: str, refresh: bool = False) -> dict:
    try:
        key = str(resolve_repo(path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if refresh or key not in _cache:
        _cache[key] = analyzer.analyze(key)
    return _cache[key]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ollama": llm.status()}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    return _get_analysis(req.path, refresh=True)


@app.post("/api/ask")
def ask(req: AskRequest) -> dict:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty")
    return investigate.ask(_get_analysis(req.path), req.question)


@app.post("/api/report")
def make_report(req: ReportRequest) -> dict:
    return {"markdown": report.build_report(_get_analysis(req.path), req.qa)}


@app.get("/api/source")
def source(path: str, file: str, line: int = Query(1, ge=1), context: int = Query(8, ge=0, le=40)) -> dict:
    try:
        root = resolve_repo(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    text = investigate.snippet(root, file, line, context)
    if not text:
        raise HTTPException(status_code=404, detail="File not found or outside repository")
    return {"file": file, "line": line, "snippet": text}
