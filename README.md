# Glasshouse

![Glasshouse report grid showing a builder archetype, model preference, productive hours, planning habits, agent usage, and prompt style](assets/glasshouse-report.png)

**See what kind of builder you are.**

Glasshouse turns your local Claude Code, Codex, and Cursor history into an interactive, Wrapped-style report about how you build: your archetype, habits, prompts, productive hours, agent usage, and shipped work.

Install it as an agent skill with [skills.sh](https://skills.sh):

```bash
npx skills add Provn-Inc/glasshouse -g
```

Then ask your agent: `Use $glasshouse to create my builder report for this month.`

## Quick start

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
cd glasshouse
uv run glasshouse --period 2026-08
uv run glasshouse serve
```

Glasshouse creates the directory automatically and writes:

```text
outputs/glasshouse-2026-08.html
outputs/glasshouse-2026-08.json
```

The HTML report is interactive and shareable. `serve` opens the newest report in your browser and listens only on `127.0.0.1`; press `Ctrl-C` to stop it.

Install the command globally from a checkout if you prefer:

```bash
uv tool install --editable .
glasshouse --period 2026
glasshouse serve
```

## Privacy

Glasshouse processes transcripts locally and does **not currently collect telemetry**.

- Raw transcripts are not uploaded or embedded in reports.
- Common keys, tokens, emails, IP addresses, and home paths are scrubbed from report text.
- Reports contain no remote assets or analytics scripts.
- Optional pull-request enrichment uses your existing authenticated `gh` session.

Reports may include selected prompt text. Review yours before sharing it, even when Glasshouse reports that no secrets were scrubbed.

## Useful commands

```bash
# Current month
uv run glasshouse

# One source only
uv run glasshouse --period 2026-08 --sources codex

# Skip Git and GitHub enrichment
uv run glasshouse --no-git --no-gh

# Print aggregate data without writing files
uv run glasshouse --dry-run

# Serve a named report without opening the browser
uv run glasshouse serve glasshouse-2026-08.html --port 8765 --no-open
```

Run `uv run glasshouse --help` for every option.

## Development

```bash
uv run python -m unittest discover -v
uv build --wheel
```

Contributions that improve source compatibility, metric accuracy, privacy, accessibility, or report design are welcome.

Glasshouse is available under the [MIT License](LICENSE).

## Built something worth showing?

Glasshouse helps you understand **how** you build. [Provn](https://provn.co) helps you show **what** you can build.

Share your Glasshouse report with friends, then bring the work you are proud of to Provn—where builders prove their skills through real work, not just claims.

**[Share what you built on Provn →](https://provn.co)**
