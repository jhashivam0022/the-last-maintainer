"""Compare API references in documentation against endpoints found in source.

Heuristics, not proof: every result is a *potential* inconsistency to verify.
"""
from __future__ import annotations

import re
from pathlib import Path

from .scanner import DOC_EXTENSIONS, read_text

_METHOD_PATH = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+`?(/[\w\-./{}:]*)")
_BARE_PATH = re.compile(r"`(/[\w\-./{}:]+)`")
_PARAM = re.compile(r"\{[^}/]*\}|:\w+")


def normalize(path: str) -> str:
    path = _PARAM.sub("{}", path.strip())
    path = path.rstrip(".,:;)")
    return "/" + path.strip("/") if path.strip("/") else "/"


def _first_segment(path: str) -> str:
    return path.strip("/").split("/", 1)[0]


def find_doc_gaps(root: Path, files: list[str], endpoints: list[dict]) -> dict:
    doc_files = [f for f in files if Path(f).suffix.lower() in DOC_EXTENSIONS]
    actual: dict[str, set[str]] = {}
    for ep in endpoints:
        actual.setdefault(normalize(ep["path"]), set()).add(ep["method"])
    known_prefixes = {_first_segment(p) for p in actual}

    references: list[dict] = []
    for rel in doc_files:
        try:
            lines = read_text(root / rel).splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            claimed = set()
            for method, path in _METHOD_PATH.findall(line):
                references.append({"file": rel, "line": number, "method": method, "path": normalize(path)})
                claimed.add(normalize(path))
            for path in _BARE_PATH.findall(line):
                norm = normalize(path)
                if norm not in claimed and _first_segment(norm) in known_prefixes:
                    references.append({"file": rel, "line": number, "method": None, "path": norm})

    documented_not_found: list[dict] = []
    for ref in references:
        methods = actual.get(ref["path"])
        if methods is None:
            documented_not_found.append({**ref, "problem": "path not found in source"})
        elif ref["method"] and ref["method"] not in methods and "ANY" not in methods:
            documented_not_found.append(
                {**ref, "problem": f"path exists but only for {', '.join(sorted(methods))}"}
            )

    documented_paths = {r["path"] for r in references}
    undocumented = (
        [ep for ep in endpoints if normalize(ep["path"]) not in documented_paths] if doc_files else []
    )
    return {
        "docs_scanned": doc_files,
        "references_found": len(references),
        "documented_not_found": documented_not_found,
        "undocumented": undocumented,
    }
