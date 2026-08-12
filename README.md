# Glasshouse

Glasshouse creates a private, local “Wrapped” report from your Claude Code,
Codex, and Cursor sessions. It streams transcripts on your machine, retains
typed prompts only for local analysis, scrubs common secrets from report text,
and produces one self-contained HTML file.

```bash
uv tool install --editable .
glasshouse --period 2026-08
```

Glasshouse creates `outputs/` automatically and writes both artifacts there:

```text
outputs/glasshouse-2026-08.html
outputs/glasshouse-2026-08.json
```

For a one-off run from a checkout, installation is optional:

```bash
uv run glasshouse --period 2026-08
```

Use `--dry-run` to print aggregate JSON, `--sources codex` to select sources,
or `--no-git --no-gh` to disable repository enrichment. No transcript upload,
telemetry, hosted account, external report assets, or JavaScript is used.

Preview the newest generated report and open it in your default browser:

```bash
uv run glasshouse serve
```

You can select a report beneath `outputs/`, choose a port, or avoid opening the
browser automatically:

```bash
uv run glasshouse serve glasshouse-2026-08.html --port 8765 --no-open
```

The preview server listens only on `127.0.0.1` and stops with Ctrl-C.

Run tests with `uv run python -m unittest discover -v`.
