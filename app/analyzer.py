"""Orchestrates the deterministic analysis and returns structured evidence."""
from __future__ import annotations

from pathlib import Path

from . import doc_gaps, git_history, java_parser, scanner

HISTORY_FILE_CAP = 60  # distinct controller files to query for history


def analyze(path: str) -> dict:
    root = scanner.resolve_repo(path)
    scan = scanner.scan(root)

    sources = {}
    for rel in scan.files:
        if rel.endswith(".java"):
            try:
                sources[rel] = scanner.read_text(root / rel)
            except OSError:
                continue
    components, endpoints, relationships = java_parser.analyze_sources(sources)

    git = git_history.is_git_repo(root)
    commits: list[dict] = []
    if git:
        commits = git_history.recent_commits(root)
        cache: dict[str, list[dict]] = {}
        for rel in sorted({ep["file"] for ep in endpoints})[:HISTORY_FILE_CAP]:
            cache[rel] = git_history.file_history(root, rel)
        for ep in endpoints:
            ep["history"] = cache.get(ep["file"], [])
    else:
        for ep in endpoints:
            ep["history"] = []

    gaps = doc_gaps.find_doc_gaps(root, scan.files, endpoints)

    result = {
        "repo": {
            "path": str(root),
            "name": root.name,
            "is_git": git,
            "file_count": len(scan.files),
            "truncated": scan.truncated,
            "languages": scan.languages,
            "key_files": scan.key_files,
            "dependencies": scan.dependencies,
            "java_files": len(sources),
        },
        "components": components,
        "endpoints": endpoints,
        "relationships": relationships,
        "commits": commits,
        "doc_gaps": gaps,
    }
    result["open_questions"] = _open_questions(result)
    return result


def _open_questions(result: dict) -> list[str]:
    questions: list[str] = []
    repo = result["repo"]
    if repo["java_files"] == 0:
        questions.append("No Java sources were found; only repository structure could be analyzed.")
    elif not result["endpoints"]:
        questions.append("Java sources exist but no Spring MVC endpoints were detected. Are routes defined another way?")
    if not repo["is_git"]:
        questions.append("The directory is not a Git repository, so no history evidence is available.")
    if repo["truncated"]:
        questions.append("The scan hit the file limit; some files were not examined.")
    gaps = result["doc_gaps"]
    if not gaps["docs_scanned"]:
        questions.append("No documentation files (.md/.rst/.txt/.adoc) were found to compare against the code.")
    related = {r["source"] for r in result["relationships"]} | {r["target"] for r in result["relationships"]}
    for comp in result["components"]:
        if comp["kind"] in {"controller", "service", "repository"} and comp["name"] not in related:
            questions.append(f"No relationships could be established for {comp['kind']} {comp['name']} ({comp['file']}:{comp['line']}).")
    if repo["is_git"]:
        for file in sorted({ep["file"] for ep in result["endpoints"] if len(ep["history"]) == 1}):
            questions.append(f"{file} has a single commit; the reason its endpoints exist is not recorded in history.")
    return questions
