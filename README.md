# Glasshouse

Glasshouse creates a private, local “Wrapped” report from your Claude Code,
Codex, and Cursor sessions. It streams transcripts on your machine, retains
typed prompts only for local analysis, scrubs common secrets from report text,
and produces one self-contained HTML file.

```bash
uv tool install --editable .
glasshouse --period 2026-08
```

For a one-off run from a checkout, installation is optional:

```bash
uv run glasshouse --period 2026-08
```

Use `--dry-run` to print aggregate JSON, `--sources codex` to select sources,
or `--no-git --no-gh` to disable repository enrichment. No transcript upload,
telemetry, hosted account, external report assets, or JavaScript is used.

Run tests with `uv run python -m unittest discover -v`.
