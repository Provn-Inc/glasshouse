---
name: glasshouse
description: Generates, inspects, and opens private Glasshouse reports about Claude Code, Codex, and Cursor activity. Use when a user wants a coding-agent month or year in review, builder archetype, usage analytics, or local interactive report.
license: MIT
compatibility: Requires uv, Python 3.11+, and network access when the Glasshouse CLI is not cached. GitHub enrichment optionally uses an authenticated gh CLI session.
metadata:
  author: Provn
  version: "0.1.0"
---

# Glasshouse

Create a private, interactive report that helps the user understand what kind
of builder they are. Keep raw coding-agent transcripts out of model context.

## Generate

1. Keep the process working directory set to the user's project. The launcher
   writes `outputs/` there and analyzes that Git repository.
2. Use the current month unless the user supplies `YYYY-MM` or `YYYY`.
3. From this skill directory, invoke the bundled launcher by absolute path:

   ```bash
   scripts/glasshouse --period YYYY-MM
   ```

4. Add `--no-gh` when the user declines authenticated GitHub enrichment. Use
   `--sources claude_code,codex,cursor` to restrict source discovery.
5. Read only the command summary and aggregate JSON beneath `outputs/`. Never
   open raw transcript JSONL or Cursor database contents in model context.
6. Return the HTML path, parsed session count, malformed lines, dropped cards,
   and secret-scrub count. Missing sources are expected; continue with others.
7. Remind the user to review the report before sharing, even when zero secrets
   were scrubbed.

Use `--dry-run` for aggregate diagnostics without writing report files.

## Open

Run the launcher from the same user project directory:

```bash
scripts/glasshouse serve
```

Add a report filename beneath `outputs/` when the user names one. The server
binds only to `127.0.0.1` and runs until interrupted. Add `--no-open` when a
browser should not open and return the local URL instead.

Read [privacy and sharing](references/privacy.md) when the user asks what data
Glasshouse reads, whether it uploads data, or whether a report is safe to post.
