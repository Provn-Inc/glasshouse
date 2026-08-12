from pathlib import Path
from .common import counter_add, finalize, jsonl, new_session, text_content
from ..model import AdapterResult, Prompt, parse_datetime


def collect(root: Path, period) -> AdapterResult:
    result = AdapterResult("claude_code")
    if not root.exists():
        result.skipped = "source directory not found"
        return result
    sessions = {}
    for path in root.rglob("*.jsonl"):
        fallback = path.stem
        for row, malformed in jsonl(path):
            if malformed:
                result.malformed_lines += 1; continue
            ts = parse_datetime(row.get("timestamp"))
            if not ts:
                continue
            sid = str(row.get("sessionId") or fallback)
            session = sessions.setdefault(sid, new_session(sid, "claude_code", ts, row))
            session.started_at = min(session.started_at, ts); session.ended_at = max(session.ended_at, ts)
            session.cwd = session.cwd or row.get("cwd"); session.git_branch = session.git_branch or row.get("gitBranch")
            if row.get("type") == "user" and row.get("promptSource", "typed") == "typed":
                text = text_content(row.get("message") or row.get("content")).strip()
                if text and period.contains(ts):
                    mode = row.get("permissionMode")
                    session.prompts.append(Prompt(text, ts, len(text.split()), mode))
                    counter_add(session.permission_modes, mode)
            if row.get("type") == "assistant":
                message = row.get("message") or {}
                counter_add(session.model_counts, message.get("model"))
                usage = message.get("usage") or {}
                session.tokens["input"] += int(usage.get("input_tokens") or 0)
                session.tokens["output"] += int(usage.get("output_tokens") or 0)
                for item in message.get("content") or []:
                    if isinstance(item, dict) and item.get("type") in {"tool_use", "function_call"}:
                        counter_add(session.tool_calls, item.get("name"))
    result.sessions = finalize(sessions, period)
    return result

