# Output Directory and Serve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route every generated artifact into `./outputs/` and add a safe `glasshouse serve` browser-preview command.

**Architecture:** A focused output-path module owns creation, containment, and newest-report discovery. A server module exposes exactly one validated HTML file over a loopback HTTP server; the CLI dispatches generation or serving without transcript collection in the serve path.

**Tech Stack:** Python 3.11+ standard library, `unittest`, `uv`.

## Global Constraints

- Generated HTML and JSON must stay beneath `./outputs/`.
- The output directory is created automatically.
- The HTTP server binds only to `127.0.0.1` and exposes only one report.
- `serve` never initializes transcript adapters or metrics collection.

---

### Task 1: Output-root enforcement

**Files:** Create `glasshouse/outputs.py`, `tests/test_outputs.py`; modify `glasshouse/cli.py`, `.gitignore`, and `README.md`.

**Interfaces:** `OutputPaths(root).resolve(candidate, suffix) -> Path`; `OutputPaths.latest_report() -> Path`.

- [ ] Write failing tests for root creation, defaults, relative names, absolute/traversal rejection, and newest-report discovery.
- [ ] Implement contained path resolution and route CLI HTML/JSON writes through it.
- [ ] Run focused and full tests, then commit.

### Task 2: Local report server

**Files:** Create `glasshouse/server.py`, `tests/test_server.py`; modify `glasshouse/cli.py` and `README.md`.

**Interfaces:** `serve_report(report, port=0, open_browser=True, browser_open=webbrowser.open) -> int`; CLI `glasshouse serve [REPORT.html] [--port PORT] [--no-open]`.

- [ ] Write failing tests for CLI parsing, loopback binding, report-only GET behavior, discovery, browser URL, Ctrl-C shutdown, and error exits.
- [ ] Implement a single-file request handler and subcommand dispatch without entering collection code.
- [ ] Run focused and full tests, manual no-open smoke test, compile, and package checks.
- [ ] Commit the verified feature.
