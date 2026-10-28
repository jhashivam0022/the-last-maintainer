"""Redact secrets before text reaches the model, the UI or an exported report."""
from __future__ import annotations

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
        "[REDACTED PRIVATE KEY]",
    ),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED AWS KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}"), "Bearer [REDACTED]"),
    # key=value / key: value lines (properties, yaml, .env)
    (
        re.compile(
            r"(?im)^([ \t]*[\w.\-]*(?:password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|credentials?)"
            r"[\w.\-]*[ \t]*[=:][ \t]*)(?!\s*$)(.+)$"
        ),
        r"\1[REDACTED]",
    ),
    # String apiKey = "abc";
    (
        re.compile(r"(?i)((?:password|passwd|secret|token|api[_-]?key)\w*\s*=\s*)\"[^\"]*\""),
        r'\1"[REDACTED]"',
    ),
    # jdbc:...?user=x&password=y
    (re.compile(r"(?i)([?&;](?:user|password)=)[^&;\s\"']+"), r"\1[REDACTED]"),
    # scheme://user:password@host
    (re.compile(r"(://[^/\s:@]+:)[^@\s/]+(@)"), r"\1[REDACTED]\2"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text
