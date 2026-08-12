from __future__ import annotations

from pathlib import Path
from . import claude_code, codex, cursor

ADAPTERS = {"claude_code": claude_code.collect, "codex": codex.collect, "cursor": cursor.collect}


def collect_sources(names, roots, period):
    results = []
    for name in names:
        try:
            results.append(ADAPTERS[name](Path(roots[name]).expanduser(), period))
        except Exception as exc:
            from ..model import AdapterResult
            results.append(AdapterResult(name, skipped=f"adapter error: {type(exc).__name__}"))
    return results

