"""Regex-based static analysis of Java / Spring Boot sources.

Sources are only read as text. Nothing is compiled or executed.
Results are facts about declarations; relationships are detected by type usage
and are reported with the file and line that support them.
"""
from __future__ import annotations

import re

STEREOTYPES = {
    "RestController": "controller",
    "Controller": "controller",
    "Service": "service",
    "Repository": "repository",
    "Entity": "entity",
    "Configuration": "configuration",
    "Component": "component",
}
HTTP_VERBS = {"Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE", "Patch": "PATCH"}

_STRING_OR_COMMENT = re.compile(r'"(?:\\.|[^"\\\n])*"|//[^\n]*|/\*.*?\*/', re.S)
_ANNO = r"@\w+(?:\((?:[^()]|\([^()]*\))*\))?"
_CLASS_RE = re.compile(
    rf"(?P<annos>(?:{_ANNO}\s*)*)(?:(?:public|protected|private|abstract|final|static)\s+)*"
    r"(?P<kind>class|interface|enum|record)\s+(?P<name>\w+)(?P<rest>[^{;]*)\{"
)
_MAPPING_RE = re.compile(
    r"@(?P<verb>Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\((?P<args>(?:[^()]|\([^()]*\))*)\))?\s*"
    rf"(?:{_ANNO}\s*)*(?:(?:public|protected|private|static|final)\s+)*"
    r"(?P<ret>[\w<>\[\]?,.\s]+?)\s+(?P<name>\w+)\s*\("
)
_REPO_BASE = re.compile(r"\b\w*Repository\s*<\s*(\w+)")


def strip_comments(text: str) -> str:
    """Blank out comments (keeping newlines so line numbers survive); keep string literals."""

    def repl(match: re.Match[str]) -> str:
        token = match.group()
        if token.startswith('"'):
            return token
        return re.sub(r"[^\n]", " ", token)

    return _STRING_OR_COMMENT.sub(repl, text)


def _match_brace(text: str, open_index: int) -> int:
    depth = 0
    i = open_index
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "'":
            i += 1
            while i < n and text[i] != "'":
                i += 2 if text[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def _annotations(block: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2) or "") for m in re.finditer(r"@(\w+)\s*(?:\(((?:[^()]|\([^()]*\))*)\))?", block)]


def _paths_from_args(args: str | None) -> list[str]:
    if not args or not args.strip():
        return [""]
    named = re.search(r"\b(?:value|path)\s*=\s*(\{[^}]*\}|\"[^\"]*\")", args)
    positional = re.match(r"\s*(\{[^}]*\}|\"[^\"]*\")", args)
    chosen = named or positional
    if not chosen:
        return [""]
    return re.findall(r'"([^"]*)"', chosen.group(1)) or [""]


def _methods_from_args(args: str | None) -> list[str]:
    if args:
        m = re.search(r"\bmethod\s*=\s*(\{[^}]*\}|[\w.]+)", args)
        if m:
            found = re.findall(r"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)", m.group(1))
            if found:
                return found
    return ["ANY"]


def join_path(*parts: str) -> str:
    segments = [p.strip("/") for p in parts if p and p.strip("/")]
    return "/" + "/".join(segments)


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def parse_file(rel: str, raw: str) -> dict:
    """Parse one Java file into classes and endpoints."""
    text = strip_comments(raw)
    package_match = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.M)
    package = package_match.group(1) if package_match else None

    classes: list[dict] = []
    for m in _CLASS_RE.finditer(text):
        annos = _annotations(m.group("annos"))
        anno_names = [a for a, _ in annos]
        kind = next((STEREOTYPES[a] for a in anno_names if a in STEREOTYPES), None)
        rest = m.group("rest")
        if kind is None and m.group("kind") == "interface" and re.search(r"\bextends\b.*\w*Repository\b", rest, re.S):
            kind = "repository"
        base_paths = [""]
        table = None
        for name, args in annos:
            if name == "RequestMapping":
                base_paths = _paths_from_args(args)
            elif name == "Table":
                t = re.search(r'\bname\s*=\s*"([^"]+)"', args)
                table = t.group(1) if t else None
        open_brace = m.end() - 1
        end = _match_brace(text, open_brace)
        entity_of = None
        if kind == "repository":
            rb = _REPO_BASE.search(rest)
            entity_of = rb.group(1) if rb else None
        classes.append(
            {
                "name": m.group("name"),
                "kind": kind or m.group("kind"),
                "file": rel,
                "line": _line_of(text, m.start("kind")),
                "package": package,
                "annotations": anno_names,
                "base_paths": base_paths,
                "table": table,
                "entity_of": entity_of,
                "_start": m.start(),
                "_end": end,
                "_body": text[open_brace : end + 1],
                "_body_offset": open_brace,
            }
        )

    endpoints: list[dict] = []
    for m in _MAPPING_RE.finditer(text):
        owner = None
        for cls in classes:  # innermost enclosing class wins
            if cls["_start"] <= m.start() < cls["_end"] and (owner is None or cls["_start"] > owner["_start"]):
                owner = cls
        if owner is None:
            continue
        verb = m.group("verb")
        args = m.group("args")
        methods = [HTTP_VERBS[verb]] if verb in HTTP_VERBS else _methods_from_args(args)
        for http_method in methods:
            for base in owner["base_paths"]:
                for sub in _paths_from_args(args):
                    endpoints.append(
                        {
                            "method": http_method,
                            "path": join_path(base, sub),
                            "controller": owner["name"],
                            "handler": m.group("name"),
                            "file": rel,
                            "line": _line_of(text, m.start()),
                        }
                    )
    return {"classes": classes, "endpoints": endpoints, "text": text}


def analyze_sources(sources: dict[str, str]) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (components, endpoints, relationships) for {relative path: source text}."""
    parsed = {rel: parse_file(rel, raw) for rel, raw in sorted(sources.items())}
    components: list[dict] = []
    endpoints: list[dict] = []
    for p in parsed.values():
        components.extend(p["classes"])
        endpoints.extend(p["endpoints"])

    by_name = {c["name"]: c for c in components}
    relationships: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(src: dict, dst: str, kind: str, rel_file: str, line: int) -> None:
        key = (src["name"], dst, kind)
        if dst == src["name"] or dst not in by_name or key in seen:
            return
        seen.add(key)
        relationships.append({"source": src["name"], "target": dst, "kind": kind, "file": rel_file, "line": line})

    for src in components:
        file_text = parsed[src["file"]]["text"]
        body = src["_body"]
        for target in by_name:
            if target == src["name"]:
                continue
            decl = re.compile(
                rf"\b{re.escape(target)}(?:<[^<>;]*>)?\s+\w+\s*[;=,)]"
                rf"|<[^<>;]*\b{re.escape(target)}\b[^<>;]*>\s*\w+\s*[;=,)]"
            )
            hit = decl.search(body)
            if hit:
                kind = "relates-to" if src["kind"] == "entity" and by_name[target]["kind"] == "entity" else "uses"
                add(src, target, kind, src["file"], _line_of(file_text, src["_body_offset"] + hit.start()))
        if src["entity_of"]:
            add(src, src["entity_of"], "manages", src["file"], src["line"])

    for c in components:
        for key in ("_start", "_end", "_body", "_body_offset"):
            c.pop(key, None)
    return components, endpoints, relationships
