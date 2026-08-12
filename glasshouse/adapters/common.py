from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable
import json

from ..model import Prompt, Session, parse_datetime


def jsonl(path: Path):
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                yield json.loads(line), False
            except (json.JSONDecodeError, UnicodeDecodeError):
                yield None, True


def text_content(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return text_content(value.get("content") or value.get("text") or value.get("message"))
    if isinstance(value, list):
        return "\n".join(filter(None, (text_content(item) for item in value)))
    return ""


def counter_add(counter: dict[str, int], key: object, amount: int = 1):
    if isinstance(key, str) and key:
        counter[key] = counter.get(key, 0) + amount


def new_session(session_id, source, ts, row=None):
    row = row or {}
    return Session(str(session_id), source, row.get("cwd"), row.get("gitRemote"), row.get("gitBranch"), ts, ts,
                   bool(row.get("isSidechain")), {}, {}, {}, {"input": 0, "output": 0}, [])


def finalize(sessions: dict[str, Session], period) -> list[Session]:
    return sorted((s for s in sessions.values() if s.prompts and any(period.contains(p.ts) for p in s.prompts)), key=lambda s: s.started_at)

