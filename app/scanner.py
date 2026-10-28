"""Repository structure scan. Reads files as text only; never executes anything."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "target", "build", "dist", "out",
    "__pycache__", ".idea", ".vscode", ".gradle", ".mvn", ".next", "coverage",
}
MAX_FILES = 20_000
MAX_READ_BYTES = 1_000_000

KEY_FILE_NAMES = {
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "package.json",
    "requirements.txt", "pyproject.toml", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "application.properties", "application.yml", "application.yaml",
    "Makefile",
}
DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}


@dataclass
class RepoScan:
    root: Path
    files: list[str] = field(default_factory=list)  # POSIX-style paths relative to root
    languages: dict[str, int] = field(default_factory=dict)
    key_files: list[str] = field(default_factory=list)
    dependencies: list[dict] = field(default_factory=list)
    truncated: bool = False


def resolve_repo(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {path}")
    return root


def safe_join(root: Path, rel: str) -> Path:
    """Resolve `rel` under `root`, refusing anything that escapes it."""
    target = (root / rel).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes the repository root")
    return target


def read_text(path: Path, limit: int = MAX_READ_BYTES) -> str:
    with open(path, "rb") as fh:
        data = fh.read(limit)
    return data.decode("utf-8", errors="replace")


def scan(root: Path) -> RepoScan:
    result = RepoScan(root=root)
    ext_counts: Counter[str] = Counter()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            if len(result.files) >= MAX_FILES:
                result.truncated = True
                break
            rel = full.relative_to(root).as_posix()
            result.files.append(rel)
            ext = full.suffix.lower()
            if ext:
                ext_counts[ext] += 1
            if name in KEY_FILE_NAMES:
                result.key_files.append(rel)
        if result.truncated:
            break
    result.languages = dict(ext_counts.most_common(12))
    result.dependencies = _collect_dependencies(root, result.key_files)
    return result


_POM_DEP = re.compile(
    r"<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>(?:\s*<version>([^<]+)</version>)?",
    re.S,
)
_GRADLE_DEP = re.compile(
    r"\b(?:implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(?\s*['\"]([^'\"]+)['\"]"
)


def _collect_dependencies(root: Path, key_files: list[str]) -> list[dict]:
    deps: list[dict] = []
    for rel in key_files:
        name = rel.rsplit("/", 1)[-1]
        try:
            text = read_text(root / rel)
        except OSError:
            continue
        if name == "pom.xml":
            for group, artifact, version in _POM_DEP.findall(text):
                deps.append({"name": f"{group.strip()}:{artifact.strip()}", "version": version.strip() or None, "source": rel})
        elif name.startswith("build.gradle"):
            for coord in _GRADLE_DEP.findall(text):
                deps.append({"name": coord, "version": None, "source": rel})
        elif name == "package.json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            for section in ("dependencies", "devDependencies"):
                for dep, version in (data.get(section) or {}).items():
                    deps.append({"name": dep, "version": str(version), "source": rel})
        elif name == "requirements.txt":
            for line in text.splitlines():
                line = line.split("#", 1)[0].strip()
                if line and not line.startswith("-"):
                    match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", line)
                    if match:
                        deps.append({"name": match.group(1), "version": match.group(2) or None, "source": rel})
    return deps
