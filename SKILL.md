---
name: glasshouse
description: Create a private local Wrapped-style HTML report from Claude Code, Codex, and Cursor coding-agent activity. Use when the user asks for Glasshouse, agent usage analytics, a coding-agent year/month in review, or a shareable local activity report.
---

# Glasshouse

Generate a report without reading raw transcript files into model context.

1. Ask for a period only if the user did not supply one; otherwise use the current month.
2. Run `python3 -m glasshouse --period YYYY-MM` from this skill directory. Pass `--no-gh` when the user does not want the optional authenticated GitHub query.
3. Read only the command summary and aggregate JSON. Never open raw transcript JSONL or Cursor databases in model context.
4. Report the HTML path, parsed session counts, dropped cards, malformed lines, and secret-scrub count.
5. Warn the user to review the artifact before public sharing even when the scrub count is zero.

Use `--dry-run` for aggregate diagnostics and `--sources claude_code,codex,cursor` to limit discovery. A missing source is expected and must not block the remaining sources.

