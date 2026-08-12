# Glasshouse

**See what kind of builder you are.**

Glasshouse turns your local coding-agent history into an interactive, Wrapped-style report about how you build: when you work, how you prompt, which models you reach for, how often you change course, what you ship, and the collaboration style that emerges along the way.

It works with Claude Code, Codex, and Cursor. Your transcripts stay on your machine.

## What you get

Glasshouse produces a self-contained HTML report made of interactive cards. The report can reveal things like:

- Your builder archetype
- Your most-used model
- Your most productive hours
- How often you plan before building
- Your typical prompt length
- Your peak number of parallel agents
- Your most cryptic prompt
- Your longest focused run
- How much code you shipped
- Your most common shipping day

Hover over a card for a little movement. Open it to see the full reading, move between cards, or link directly to one with its URL hash.

## Privacy by design

Glasshouse is built for local analysis.

- Transcript files are streamed and processed on your machine.
- Raw transcripts are not uploaded to Glasshouse or placed in the generated report.
- Common API keys, tokens, email addresses, IP addresses, and home-directory paths are scrubbed from report text.
- Reports contain inline CSS, SVG, and JavaScript, with no remote assets or analytics scripts.
- The preview server binds only to `127.0.0.1` and exposes only the selected report.
- GitHub pull-request enrichment is optional and uses your existing authenticated `gh` CLI session.

Glasshouse does **not currently collect telemetry**. Because reports may contain selected prompt text, review yours before sharing it publicly—even when Glasshouse reports that no secrets were scrubbed.

## Requirements

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Optional: Git for shipping statistics
- Optional: the GitHub CLI (`gh`) for pull-request statistics

## Quick start

From a repository checkout, run Glasshouse directly with `uv`:

```bash
cd glasshouse
uv run glasshouse
```

With no period supplied, Glasshouse analyzes the current calendar month. To generate a report for a specific month or year:

```bash
uv run glasshouse --period 2026-08
uv run glasshouse --period 2026
```

Glasshouse creates `outputs/` automatically:

```text
outputs/
├── glasshouse-2026-08.html
└── glasshouse-2026-08.json
```

The HTML file is the shareable report. The JSON file contains the scrubbed aggregate data used to build it.

## Open your report

Serve the newest report and open it in your default browser:

```bash
uv run glasshouse serve
```

Serve a specific report, choose a stable port, or skip opening the browser automatically:

```bash
uv run glasshouse serve glasshouse-2026-08.html
uv run glasshouse serve --port 8765 --no-open
```

Press `Ctrl-C` to stop the local server.

## Install the command

If you want `glasshouse` available outside the repository, install the checkout as an editable `uv` tool:

```bash
uv tool install --editable .
glasshouse --period 2026-08
glasshouse serve
```

## Useful options

```text
--period YYYY-MM|YYYY        Analyze a calendar month or year
--sources SOURCE,...         Use claude_code, codex, cursor, or a subset
--out PATH                   Choose an HTML path beneath outputs/
--json-out PATH              Choose a JSON path beneath outputs/
--no-git                     Skip local Git statistics
--no-gh                      Skip optional GitHub CLI statistics
--dry-run                    Print scrubbed aggregate JSON without writing files
```

Examples:

```bash
# Analyze only Codex sessions
uv run glasshouse --period 2026-08 --sources codex

# Generate without repository or GitHub enrichment
uv run glasshouse --period 2026-08 --no-git --no-gh

# Inspect aggregate data without creating a report
uv run glasshouse --period 2026-08 --dry-run
```

Run `uv run glasshouse --help` or `uv run glasshouse serve --help` for the complete command reference.

## How it works

1. Source adapters stream local Claude Code, Codex, and Cursor session records.
2. Each source is normalized into a shared session model.
3. Glasshouse filters activity to the selected calendar period.
4. Deterministic metrics calculate the report cards and supporting detail.
5. Optional local Git data adds commit, line-change, and shipping-day cards.
6. Sensitive patterns are scrubbed from every string that reaches the output.
7. A self-contained interactive HTML report and its aggregate JSON are written to `outputs/`.

Missing sources, malformed records, unavailable tools, and insufficient data produce a partial report instead of stopping the entire run. Cards without enough evidence are omitted rather than filled with misleading zeroes.

## Development

Run the test suite:

```bash
uv run python -m unittest discover -v
```

Build a wheel:

```bash
uv build --wheel
```

The implementation uses the Python standard library. Contributions that improve source compatibility, metric accuracy, privacy, accessibility, or report design are welcome. Please include focused tests and keep the generated report self-contained.

## License

Glasshouse is available under the [MIT License](LICENSE).

## Built something worth showing?

Glasshouse helps you understand **how** you build. [Provn](https://provn.co) helps you show **what** you can build.

We encourage you to share your Glasshouse report with friends and bring the work you are proud of to Provn—a place for builders to prove their skills through real work, not just claims.

**[Share what you have built on Provn →](https://provn.co)**
