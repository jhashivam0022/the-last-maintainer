"""Evidence retrieval and grounded question answering."""
from __future__ import annotations

import re
from pathlib import Path

from . import llm
from .redact import redact
from .scanner import read_text, safe_join

STOPWORDS = {
    "the", "and", "for", "how", "what", "why", "does", "this", "that", "with", "from", "are", "was",
    "who", "where", "when", "which", "can", "work", "works", "use", "used", "about", "into", "any",
}
MAX_EVIDENCE = 8

SYSTEM_PROMPT = (
    "You are an assistant that explains a legacy codebase using ONLY the numbered evidence provided. "
    "Cite evidence ids like [E1] after every claim. Separate your answer into 'Verified' (directly stated "
    "by evidence), 'Plausible' (reasonable inference, say it is an inference) and 'Unknown' (what the "
    "evidence cannot answer). If the evidence is insufficient, say so. Never invent files, endpoints or commits."
)


def snippet(root: Path, rel: str, line: int, context: int = 6) -> str:
    try:
        lines = redact(read_text(safe_join(root, rel))).splitlines()
    except (OSError, ValueError):
        return ""
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    return "\n".join(f"{n + 1:>4}  {lines[n]}" for n in range(start, end))


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9]{2,}", re.sub(r"([a-z])([A-Z])", r"\1 \2", text))
    return {w.lower() for w in words} - STOPWORDS


def _candidates(analysis: dict) -> list[dict]:
    items: list[dict] = []
    for ep in analysis["endpoints"]:
        items.append(
            {
                "type": "endpoint",
                "title": f"{ep['method']} {ep['path']} -> {ep['controller']}.{ep['handler']}",
                "file": ep["file"],
                "line": ep["line"],
            }
        )
    for comp in analysis["components"]:
        if comp["kind"] in {"controller", "service", "repository", "entity", "component", "configuration"}:
            extra = f" (table {comp['table']})" if comp.get("table") else ""
            items.append({"type": comp["kind"], "title": f"{comp['kind']} {comp['name']}{extra}", "file": comp["file"], "line": comp["line"]})
    for rel in analysis["relationships"]:
        items.append(
            {"type": "relationship", "title": f"{rel['source']} {rel['kind']} {rel['target']}", "file": rel["file"], "line": rel["line"]}
        )
    for commit in analysis["commits"]:
        items.append({"type": "commit", "title": f"commit {commit['short']} {commit['subject']} ({commit['author']}, {commit['date'][:10]})", "commit": commit["hash"]})
    for gap in analysis["doc_gaps"]["documented_not_found"]:
        items.append(
            {
                "type": "doc-gap",
                "title": f"{gap['file']} documents {(gap['method'] or 'ANY')} {gap['path']}: {gap['problem']}",
                "file": gap["file"],
                "line": gap["line"],
            }
        )
    return items


def retrieve(analysis: dict, question: str) -> list[dict]:
    wanted = _tokens(question)
    scored = []
    for item in _candidates(analysis):
        haystack = _tokens(item["title"] + " " + item.get("file", ""))
        score = len(wanted & haystack)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: -pair[0])
    evidence = []
    for number, (_, item) in enumerate(scored[:MAX_EVIDENCE], start=1):
        entry = {**item, "id": f"E{number}"}
        if "file" in entry:
            entry["snippet"] = snippet(Path(analysis["repo"]["path"]), entry["file"], entry["line"])
        evidence.append(entry)
    return evidence


def ask(analysis: dict, question: str) -> dict:
    evidence = retrieve(analysis, question)
    if not evidence:
        return {
            "answer": None,
            "evidence": [],
            "llm_available": None,
            "note": "No evidence in the analysis matches this question, so no answer is given. Try naming a class, endpoint or file.",
        }
    context = "\n\n".join(
        f"[{e['id']}] {e['type']}: {e['title']}" + (f"\nFile: {e['file']}:{e['line']}\n{e['snippet']}" if e.get("snippet") else "")
        for e in evidence
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Evidence:\n{context}\n\nQuestion: {question}"},
    ]
    try:
        answer = llm.chat(messages)
    except llm.LLMUnavailable as exc:
        return {
            "answer": None,
            "evidence": evidence,
            "llm_available": False,
            "note": f"Local model unavailable ({exc}). Showing the retrieved evidence only.",
        }
    return {"answer": answer, "evidence": evidence, "llm_available": True, "note": "AI-generated; verify against the cited evidence."}
