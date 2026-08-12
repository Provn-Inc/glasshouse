from pathlib import Path
import shutil, sqlite3, tempfile
from .common import finalize, jsonl, new_session, text_content
from ..model import AdapterResult, Prompt, parse_datetime


def _consume(row, fallback, sessions, period):
    role = row.get("role") or row.get("type")
    if role not in {"user", "human", "user_message"}: return
    ts = parse_datetime(row.get("timestamp") or row.get("createdAt"))
    text = text_content(row.get("content") or row.get("message")).strip()
    if not ts or not text or not period.contains(ts): return
    sid = str(row.get("sessionId") or row.get("conversationId") or fallback)
    session = sessions.setdefault(sid, new_session(sid, "cursor", ts, row))
    session.prompts.append(Prompt(text, ts, len(text.split())))
    session.started_at = min(session.started_at, ts); session.ended_at = max(session.ended_at, ts)


def collect(root: Path, period) -> AdapterResult:
    result = AdapterResult("cursor")
    if not root.exists(): result.skipped = "source directory not found"; return result
    sessions = {}
    for path in root.rglob("*.jsonl"):
        for row, malformed in jsonl(path):
            if malformed: result.malformed_lines += 1
            elif isinstance(row, dict): _consume(row, path.stem, sessions, period)
    for db in root.rglob("state.vscdb"):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                copy = Path(tmp) / "state.vscdb"; shutil.copy2(db, copy)
                connection = sqlite3.connect(copy)
                for _, value in connection.execute("SELECT key, value FROM ItemTable"):
                    try:
                        import json
                        decoded = json.loads(value)
                        items = decoded if isinstance(decoded, list) else [decoded]
                        for item in items:
                            if isinstance(item, dict): _consume(item, db.stem, sessions, period)
                    except (ValueError, TypeError): pass
                connection.close()
        except (sqlite3.Error, OSError): pass
    result.sessions = finalize(sessions, period)
    return result
