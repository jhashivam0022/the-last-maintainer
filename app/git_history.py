"""Read-only Git history inspection via the git CLI (no shell, no repo code executed)."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .redact import redact

_SEP = "\x1f"
_FORMAT = f"%H{_SEP}%an{_SEP}%aI{_SEP}%s"
_HASH = re.compile(r"^[0-9a-f]{7,40}$")


def _git(root: Path, *args: str) -> str | None:
    cmd = ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def is_git_repo(root: Path) -> bool:
    return (_git(root, "rev-parse", "--is-inside-work-tree") or "").strip() == "true"


def _parse(output: str | None) -> list[dict]:
    commits = []
    for line in (output or "").splitlines():
        parts = line.split(_SEP)
        if len(parts) == 4 and _HASH.match(parts[0]):
            commits.append(
                {"hash": parts[0], "short": parts[0][:8], "author": parts[1], "date": parts[2], "subject": redact(parts[3])}
            )
    return commits


def recent_commits(root: Path, limit: int = 30) -> list[dict]:
    return _parse(_git(root, "log", f"-n{int(limit)}", f"--format={_FORMAT}", "--", "."))


def file_history(root: Path, rel_file: str, limit: int = 5) -> list[dict]:
    return _parse(_git(root, "log", f"-n{int(limit)}", "--follow", f"--format={_FORMAT}", "--", rel_file))
