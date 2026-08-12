from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class ScrubResult:
    value: object
    count: int


PATTERNS = [
    (re.compile(r"\b(?:sk-|ghp_|github_pat_|AKIA|xoxb-|yk_)[A-Za-z0-9_\-]{12,}\b"), "[api-key]"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}", re.I), "Bearer [token]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "[jwt]"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[email]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[ip-address]"),
]


def scrub(value, home: Path | None = None) -> ScrubResult:
    count = 0
    home_text = str((home or Path.home()).expanduser())
    def visit(item):
        nonlocal count
        if isinstance(item, str):
            text = item
            if home_text and home_text in text:
                occurrences = text.count(home_text); count += occurrences; text = text.replace(home_text, "~")
            for pattern, replacement in PATTERNS:
                text, hits = pattern.subn(replacement, text); count += hits
            return text
        if isinstance(item, dict): return {key: visit(val) for key, val in item.items()}
        if isinstance(item, list): return [visit(val) for val in item]
        return item
    return ScrubResult(visit(value), count)

