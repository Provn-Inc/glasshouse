from pathlib import Path
from .common import counter_add, finalize, jsonl, new_session, text_content
from ..model import AdapterResult, Prompt, parse_datetime


def collect(root: Path, period) -> AdapterResult:
    result = AdapterResult("codex")
    if not root.exists():
        result.skipped = "source directory not found"; return result
    sessions = {}
    for path in root.rglob("*.jsonl"):
        current = path.stem
        for row, malformed in jsonl(path):
            if malformed:
                result.malformed_lines += 1; continue
            ts = parse_datetime(row.get("timestamp")); payload = row.get("payload") or {}
            if not ts: continue
            if row.get("type") == "session_meta": current = str(payload.get("id") or current)
            session = sessions.setdefault(current, new_session(current, "codex", ts, payload))
            session.started_at = min(session.started_at, ts); session.ended_at = max(session.ended_at, ts)
            session.cwd = session.cwd or payload.get("cwd")
            kind = payload.get("type")
            if row.get("type") == "event_msg" and kind == "user_message":
                text = text_content(payload.get("message")).strip()
                if text and period.contains(ts): session.prompts.append(Prompt(text, ts, len(text.split()), payload.get("approval_policy")))
            elif row.get("type") == "turn_context":
                counter_add(session.model_counts, payload.get("model")); counter_add(session.permission_modes, payload.get("approval_policy"))
            elif row.get("type") == "response_item" and kind in {"function_call", "custom_tool_call"}:
                counter_add(session.tool_calls, payload.get("name"))
            usage = payload.get("usage") or payload.get("token_usage") or {}
            session.tokens["input"] += int(usage.get("input_tokens") or usage.get("input") or 0)
            session.tokens["output"] += int(usage.get("output_tokens") or usage.get("output") or 0)
    result.sessions = finalize(sessions, period)
    return result

