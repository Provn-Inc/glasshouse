---
name: glasshouse
description: Use when the user asks for Glasshouse, coding-agent usage analytics, an agent year or month in review, or a local activity report preview.
---

# Glasshouse

Generate a report without reading raw transcript files into model context.

1. Ask for a period only if the user did not supply one; otherwise use the current month.
2. Run `uv run glasshouse --period YYYY-MM` from this skill directory. Pass `--no-gh` when the user does not want the optional authenticated GitHub query.
3. Read only the command summary and aggregate JSON. Never open raw transcript JSONL or Cursor databases in model context.
4. Report the HTML path beneath `outputs/`, parsed session counts, dropped cards, malformed lines, and secret-scrub count.
5. Warn the user to review the artifact before public sharing even when the scrub count is zero.

Use `--dry-run` for aggregate diagnostics and `--sources claude_code,codex,cursor` to limit discovery. A missing source is expected and must not block the remaining sources.

When the user asks to view or preview a report, run `uv run glasshouse serve`
to open the newest report. Pass a report filename beneath `outputs/` when the
user names one. The server is local-only and runs until Ctrl-C.
