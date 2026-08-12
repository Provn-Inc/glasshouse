# Glasshouse — Design

**Date:** 2026-08-10
**Status:** Approved for planning

## Summary

A local agent skill and `glasshouse` CLI that reads a user's coding-agent transcripts, computes
statistics about how they work, and renders a self-contained HTML "wrapped"
report of 15 cards.

Everything runs on the user's machine. The only network call in the design is an
optional `gh` invocation against the user's own authenticated GitHub account.
Transcripts are never sent anywhere.

This is a local reimplementation of the idea behind YC Paxel's upload script,
which sends transcript excerpts to a hosted LLM proxy and uploads the resulting
report. This design deliberately keeps both steps local.

## Goals

- Parse agent transcripts from Claude Code, Codex, and Cursor.
- Compute 15 card metrics for a calendar period.
- Render a shareable, self-contained HTML report.
- Never load raw transcripts into model context.
- Degrade gracefully when a source, tool, or metric is unavailable.

## Non-goals

- No upload, telemetry, or account system.
- No Docker.
- No comparison against other users or cohorts.
- No historical trend tracking across reports (each run is standalone).

## Key constraint

The reference dataset is ~189 MB across ~1,280 sessions (1,166 Claude Code
transcripts at 81 MB; 111 Codex sessions at 108 MB; Cursor effectively empty).

Raw transcripts must never enter model context. A Python script performs all
extraction and aggregation, emitting a ~50 KB JSON document. Only that document
is read by the model.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Output format | Self-contained HTML, flat aesthetic | Shareable and screenshot-ready; flat styling is faster to build and easier to restyle than the reference's dithered/rotated treatment |
| Sources | Claude Code + Codex + Cursor | User elected full coverage; makes the skill useful to Cursor users even though the reference machine has no Cursor data |
| Git data | Local `git log` + optional `gh` PR counts | Enables the concrete lines/commits/PR cards; `gh` hits the user's own account, not a third party |
| Period | Calendar period (`YYYY-MM` or `YYYY`), defaulting to the current calendar month | Reads most naturally as a Wrapped-style artifact |
| Quoting | Verbatim with secret scrubbing | Verbatim quotes are what make the humor cards land; scrubbing protects a shared screenshot |
| Architecture | Script extracts, Claude narrates | Deterministic numbers with personal copy, at one cheap LLM pass |

## Architecture

### Location

Real directory at `~/.agents/skills/agent-wrapped/`, symlinked from
`~/.claude/skills/agent-wrapped`, matching the existing convention in the user's
skills directory.

### Layout

```
glasshouse/
  SKILL.md
  scripts/
    collect.py                 entry point used by the glasshouse launcher
    adapters/
      __init__.py              adapter registry
      claude_code.py
      codex.py
      cursor.py
    model.py                   NormalizedSession, Prompt
    metrics.py                 the 11 deterministic cards
    gitstats.py                git log + optional gh
    scrub.py                   secret redaction
    render.py                  JSON + template -> HTML
  templates/
    report.html
  references/
    card-catalog.md
    schemas.md
  tests/
    fixtures/
    test_*.py
```

### Data flow

1. User invokes the skill, optionally naming a period.
2. Claude runs `python3 scripts/collect.py --period YYYY-MM --out <path>`.
3. `collect.py` dispatches to each adapter; each yields `NormalizedSession`
   objects. Failures in one adapter never abort the others.
4. Sessions are filtered to the period.
5. `metrics.py` computes deterministic cards and builds shortlists for the
   judgment cards.
6. `gitstats.py` discovers repos from session `cwd` values and collects commit
   stats; optionally queries `gh` for merged PR counts.
7. `scrub.py` redacts secrets from every quoted string.
8. `wrapped-data.json` is written.
9. Claude reads the JSON, writes copy for the four judgment cards, and selects
   quotes from the shortlists.
10. `render.py` merges card content into the template and writes
    `./glasshouse-<period>.html`.
11. Claude reports the output path and the run summary.

### Normalized session model

Every adapter emits this shape. All format-specific handling is confined to the
adapter; nothing downstream knows which tool a session came from.

```python
@dataclass
class Prompt:
    text: str
    ts: datetime
    word_count: int
    permission_mode: str | None
    is_typed: bool          # a real human prompt, not a tool result or SDK turn

@dataclass
class Session:
    id: str
    source: str             # "claude_code" | "codex" | "cursor"
    cwd: str | None
    git_remote: str | None
    git_branch: str | None
    started_at: datetime
    ended_at: datetime
    is_sidechain: bool      # subagent rather than a top-level session
    model_counts: dict[str, int]
    permission_modes: dict[str, int]
    tool_calls: dict[str, int]
    tokens: dict[str, int]  # {"input": n, "output": n}
    prompts: list[Prompt]
```

Adding a fourth tool later means one new adapter file and a registry entry. No
changes to metrics, scrubbing, or rendering.

### Source specifics

**Claude Code** — `~/.claude/projects/<encoded-cwd>/<session>.jsonl`. One JSON
object per line. Human prompts are `type == "user"` with
`promptSource == "typed"`; `sdk`, `system`, and `queued` are excluded.
Per-line fields of interest: `timestamp`, `cwd`, `gitBranch`, `sessionId`,
`isSidechain`, `permissionMode`, and for assistant lines `message.model` and
`message.usage`.

**Codex** — `~/.codex/sessions/**/*.jsonl`. Different schema from Claude Code;
the adapter maps it onto the same model. Notably larger files per session, so
the adapter streams line-by-line rather than loading whole files.

**Cursor** — two possible stores: `~/.cursor/projects/<encoded>/agent-transcripts/*.jsonl`
(plain JSONL, current versions) and `workspaceStorage/<hash>/state.vscdb`
(SQLite, older versions). The adapter reads both. SQLite files are copied to a
temp path before opening, because Cursor holds a lock while running.

### Memory strategy

All adapters stream. No file is read whole. Sessions are reduced to their
`Session` record as they are parsed; prompt text is retained only for typed
prompts, and only up to a per-session cap, since the quote shortlists need at
most a few hundred candidates across the entire corpus.

## Card catalog

`D` = deterministic. `J` = model judgment. `J*` = script shortlists, model
selects.

| # | id | Question | Kind | Definition |
|---|---|---|---|---|
| 1 | `archetype` | Which archetype are you? | J | Model picks one of the 8 archetypes below from the full stat block |
| 2 | `model_mix` | Which model do you use most? | D | Assistant turns grouped by `message.model`; percentage of sessions each model dominates; top two reported |
| 3 | `peak_hours` | When are you most productive? | D | Histogram of typed-prompt timestamps by local hour; modal 4-hour window plus peak hour |
| 4 | `plan_mode` | How often do you plan? | D | User turns with `permissionMode == "plan"` divided by all typed user turns |
| 5 | `go_to_prompt` | What's your go-to prompt? | D | Normalized typed prompts; most frequent exact repeat spanning at least 3 distinct sessions |
| 6 | `parallel_agents` | How many agents do you run? | D | Maximum number of sessions with overlapping `[started_at, ended_at]`; distinct repos in that window |
| 7 | `prompt_length` | How long are your prompts? | D | Word-count distribution over typed prompts; headline is the share under 10 words |
| 8 | `cryptic_prompt` | Your most cryptic prompt? | J* | Shortlist ~20 ranked by brevity, typo ratio, absence of repo nouns, and odd hour |
| 9 | `politeness` | How polite are you to your agent? | D | Thanks/please/sorry matches in typed prompts, as a rate per 100 prompts |
| 10 | `course_change` | How often do you change course? | D | Typed prompts matching redirect patterns or arriving mid-assistant-turn, expressed as N in 10 |
| 11 | `longest_run` | What's your longest agent run? | D | Longest contiguous session; a gap over 15 minutes splits a run |
| 12 | `crash_out` | What's your biggest crash out? | J* | Shortlist ~20 ranked by caps ratio, exclamation count, profanity, word repetition |
| 13 | `shipped` | How much did you ship? | D+git | `git log --numstat` filtered to the user's author emails: insertions, commit count, merged PRs via `gh` |
| 14 | `agent_relationship` | How do you see your agent? | J | Model infers from question ratio, pushback frequency, delegation depth |
| 15 | `ship_day` | When do you ship most? | D+git | Commits grouped by weekday; modal day |

### Archetype set

Fixed at 8. The model picks the best fit and justifies it in two lines; it may
not invent new ones. Signals are indicative, not thresholds — the model weighs
the whole stat block.

| Archetype | Dominant signals |
|---|---|
| The Architect | High plan-mode share, long prompts, low course-change rate |
| The Sprinter | Short prompts, low plan-mode share, many short sessions |
| The Conductor | High parallel-agent count spanning many repos |
| The Skeptic | High course-change rate, frequent mid-turn redirects |
| The Craftsperson | Long runs, few repos, high edit-to-write ratio |
| The Explorer | Many distinct repos, read/search-heavy tool mix |
| The Delegator | Heavy subagent use, low direct editing |
| The Firefighter | Bursty activity, short runs, high crash-out signal |

These are deliberately orthogonal to the other cards. None of them keys on time
of day, which belongs to card 3.

### Deliberate departures from the reference report

**Card 3 uses prompt timestamps, not commit times.** The reference derives
"night owl" from commits. Transcript timestamps are far better powered (~1,280
sessions versus a sparser commit history) and work for users who commit rarely.

**Card 10 is explicitly approximate.** Redirect-pattern matching produces false
positives such as "no, that's right". The JSON carries the raw matched count and
the rendered copy always hedges ("about 4 in 10"). It must never state a
false-precision figure.

### Minimum-data guards

Each card declares a threshold. Below it, the card is **dropped from the grid**
rather than rendered empty or zeroed.

| Card | Threshold |
|---|---|
| `go_to_prompt` | repeat spans >= 3 sessions |
| `parallel_agents` | >= 2 overlapping sessions |
| `shipped` | >= 1 attributed commit |
| `ship_day` | >= 5 attributed commits |
| `crash_out`, `cryptic_prompt` | >= 1 shortlist candidate |
| all others | >= 10 typed prompts in period |

A report with 11 honest cards is better than 15 with four hollow ones. This is
also what makes the skill usable for someone with two weeks of history.

### Author identity for git

Union of:
- `git config user.email` in each discovered repo, and
- any author email on a commit whose SHA appears in session transcripts.

This attributes correctly in repos configured with a different email.

## Secret scrubbing

Applied to every string that reaches the report — quotes, the go-to prompt, and
any model-authored copy that echoes user text.

Patterns: common API key prefixes (`sk-`, `ghp_`, `github_pat_`, `AKIA`,
`xoxb-`, `yk_`), bearer tokens, JWTs, email addresses, IPv4 addresses, and
absolute paths under the user's home directory (replaced with `~/...`).

Scrubbing is **counted and reported** in the run summary, so the user knows
whether anything was touched before sharing the artifact. A scrub replaces the
match with a typed placeholder such as `[api-key]`, preserving readability.

## Rendering

Self-contained HTML: inline CSS and SVG, no external assets, no CDN references,
and no JavaScript. A system font stack and high-contrast typography keep it
portable. The visual direction is an editorial orange-and-paper poster: a loose
five-column stack of thin outlined cards, alternating warm orange tones, subtle
offset rotations, and generated halftone fields in each card header. CSS grid
reflows from five-wide to one-wide; reduced-motion and print styles remove
unnecessary transforms. Decorative texture never carries information.

Output path defaults to `./glasshouse-<period>.html`, overridable with
`--out`.

`render.py` owns templating. Claude contributes only the card *content* for the
four judgment cards, handed back as JSON; it never writes HTML directly. This
keeps the golden-file test meaningful and guarantees that a malformed model
response cannot produce broken markup.

## Error handling

The governing rule: **partial report, never a crash.**

| Condition | Behavior |
|---|---|
| Source directory absent | Skip; note in summary |
| Corrupt JSONL line | Skip line; count; report total |
| Cursor SQLite locked | Copy to temp and read the copy |
| `gh` missing or unauthenticated | Drop the PR figure; card 13 still renders lines and commits |
| `git` unavailable | Drop cards 13 and 15 |
| A single adapter raises | Log, continue with remaining adapters |
| Zero sessions in period | Clear error naming the period; suggest `--period` |

Every run ends with a summary: sessions parsed per source, cards dropped and
why, malformed lines skipped, secrets scrubbed.

## Testing

- **Adapter tests**, fixture-based, one per source. Highest value for Cursor,
  where synthetic fixtures are the only available validation because the
  reference machine has no Cursor history.
- **Metric tests** asserting against hand-computed values on a small fixture
  corpus.
- **Guard tests** confirming each card drops below its threshold.
- **Scrubber tests** covering every supported key format, plus a negative test
  that ordinary prose is not mangled.
- **Golden-file test** pinning the HTML render for a fixed input.
- **`--dry-run`** prints the stat block without rendering; doubles as the manual
  sanity check on real data.

## CLI contract

```
python3 scripts/collect.py [--period YYYY-MM | YYYY] [--out PATH]
                           [--sources claude_code,codex,cursor]
                           [--no-git] [--no-gh] [--dry-run]
```

`--period` defaults to the current calendar month. `--sources` defaults to all
three. `--dry-run` prints the stat block and exits without writing JSON or HTML.

## Implementation sequencing

Build in this order so each phase is independently verifiable:

1. `model.py` + `claude_code.py` adapter + fixtures — largest corpus, richest
   schema, proves the normalized model.
2. `metrics.py` for the deterministic cards, with guard tests.
3. `render.py` + template + golden-file test. End-to-end report exists here.
4. `scrub.py`, wired into every quoted string.
5. `gitstats.py`, including the `gh`-absent path.
6. `codex.py` adapter.
7. `cursor.py` adapter, fixture-only validation.
8. `SKILL.md` and the judgment-card prompt contract.

Phases 1-3 produce a working report from Claude Code data alone. Everything
after is additive.

## Known open item

The Codex JSONL field mapping must be read off real files before `codex.py` is
written. This is a discovery task in phase 6, not an unresolved design question
— the normalized model already fixes the target shape.
