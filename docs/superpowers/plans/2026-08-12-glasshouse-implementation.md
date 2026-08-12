# Glasshouse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable, privacy-first `glasshouse` CLI and agent skill that turns local Claude Code, Codex, and Cursor activity into a self-contained HTML report.

**Architecture:** Source adapters stream tool-specific records into a small normalized model. Pure metric and scrubbing modules produce JSON-safe report data; Git enrichment is optional; a deterministic renderer turns finalized cards into one portable HTML file.

**Tech Stack:** Python 3.11+ standard library, `unittest`, HTML/CSS/SVG, setuptools.

## Global Constraints

- Raw transcript files are streamed and never copied into model context or sent over a network.
- GitHub access is opt-in through the user's existing `gh` authentication; `--no-gh` disables it.
- Missing sources, malformed records, unavailable Git tools, and insufficient card data produce an honest partial report.
- Output is self-contained HTML with no remote assets or JavaScript.
- Product, package, executable, skill, and output prefix are all `glasshouse`.

---

### Task 1: Package, normalized model, periods, and CLI shell

**Files:** Create `pyproject.toml`, `glasshouse/__init__.py`, `glasshouse/__main__.py`, `glasshouse/cli.py`, `glasshouse/model.py`, `tests/test_cli.py`, `tests/test_model.py`.

**Interfaces:** `Period.parse(str | None)`, `Period.contains(datetime)`, `main(argv) -> int`, and console script `glasshouse = glasshouse.cli:main`.

- [ ] Write tests for month/year parsing, invalid periods, help, and dry-run argument handling; run them and confirm missing imports fail.
- [ ] Add the minimal package/model/parser implementation; run the focused tests until green.
- [ ] Commit the independently runnable CLI shell.

### Task 2: Streaming transcript adapters

**Files:** Create `glasshouse/adapters/{__init__,claude_code,codex,cursor}.py`, `tests/fixtures/*`, and `tests/test_adapters.py`.

**Interfaces:** Each adapter exposes `collect(root: Path, period: Period) -> AdapterResult`; registry exposes `collect_sources(names, roots, period)` and isolates adapter exceptions.

- [ ] Write synthetic JSONL/SQLite fixtures and failing tests for typed-prompt filtering, timestamps, usage, tools, sidechains, malformed lines, locked-safe SQLite copying, and unavailable roots.
- [ ] Implement line-streaming parsers and normalization without retaining assistant content; run adapter tests until green.
- [ ] Commit all three adapters and registry behavior.

### Task 3: Deterministic metrics and privacy scrubber

**Files:** Create `glasshouse/metrics.py`, `glasshouse/scrub.py`, `tests/test_metrics.py`, and `tests/test_scrub.py`.

**Interfaces:** `compute_metrics(sessions) -> MetricResult`, `scrub(value, home) -> ScrubResult`; metric results contain deterministic cards, judgment shortlists, dropped-card reasons, and a compact stat block.

- [ ] Write failing hand-computed tests for cards 2–12, thresholds, overlap, 15-minute run splitting, repeat prompts, and each documented secret pattern.
- [ ] Implement only the pure calculations and recursive scrubber needed by the tests; run focused and full tests until green.
- [ ] Commit deterministic analysis and privacy protections.

### Task 4: Git enrichment

**Files:** Create `glasshouse/gitstats.py` and `tests/test_gitstats.py`.

**Interfaces:** `collect_git_stats(repos, period, include_gh, runner) -> GitStats`; the injected runner makes subprocess behavior testable without a network.

- [ ] Write failing tests for repository discovery, author-email union, numstat totals, weekdays, and graceful missing/unauthenticated `git`/`gh` paths.
- [ ] Implement bounded subprocess calls and merge Git cards into metric output; run focused and full tests until green.
- [ ] Commit optional Git enrichment.

### Task 5: Poster renderer and report finalization

**Files:** Create `glasshouse/render.py`, `glasshouse/templates/report.html`, `tests/fixtures/report-data.json`, `tests/test_render.py`, and `tests/golden/report.html`.

**Interfaces:** `render_report(report, output_path) -> Path`; deterministic inline SVG halftones are seeded by card ID and all dynamic strings are HTML escaped.

- [ ] Write failing tests for escaping, no external resources/scripts, card omission, deterministic output, accessibility landmarks, responsive CSS, and the golden file.
- [ ] Implement the orange editorial card grid, print/reduced-motion behavior, and atomic output writing; run focused and full tests until green.
- [ ] Commit the verified self-contained renderer.

### Task 6: End-to-end collection and skill packaging

**Files:** Modify `glasshouse/cli.py`; create `SKILL.md`, `agents/openai.yaml`, `references/card-catalog.md`, `references/schemas.md`, `README.md`, `.gitignore`, and `tests/test_e2e.py`.

**Interfaces:** `glasshouse [--period YYYY-MM|YYYY] [--out PATH] [--json-out PATH] [--sources ...] [--no-git] [--no-gh] [--dry-run]`; non-dry runs write JSON and HTML, dry runs print only aggregate JSON.

- [ ] Write a failing isolated-home end-to-end test covering partial sources, JSON/HTML outputs, summaries, and zero-session exit behavior.
- [ ] Wire collection → metrics → Git → scrub → judgment fallbacks → rendering, then add concise skill instructions and generated UI metadata.
- [ ] Run tests, CLI help, fixture dry-run, package build/install smoke test, and skill validation; fix every failure.
- [ ] Commit the completed tool and documentation.

### Task 7: Final validation and review

**Files:** Inspect all changed files; modify only when a reproduced issue requires it.

- [ ] Run `python3 -m unittest discover -v`, `python3 -m compileall -q glasshouse`, package build, clean-environment install, and CLI smoke tests.
- [ ] Render the golden report and inspect it at desktop and narrow widths.
- [ ] Review the diff against every design requirement, scan for secrets/placeholders, and resolve material findings.
- [ ] Commit any verified corrections and report exact commands/results.
