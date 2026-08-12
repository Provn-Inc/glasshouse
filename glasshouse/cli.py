from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from .adapters import ADAPTERS, collect_sources
from .gitstats import collect_git_stats
from .metrics import compute_metrics
from .model import Period
from .render import render_report
from .scrub import scrub


def parser():
    p = argparse.ArgumentParser(prog="glasshouse", description="Your coding-agent work, reflected back. Private and local.")
    p.add_argument("--period", help="Calendar month (YYYY-MM) or year (YYYY); defaults to current month")
    p.add_argument("--out", type=Path, help="HTML output path")
    p.add_argument("--json-out", type=Path, help="Aggregate JSON output path")
    p.add_argument("--sources", default="claude_code,codex,cursor", help="Comma-separated: claude_code,codex,cursor")
    p.add_argument("--claude-root", type=Path, default=Path.home()/".claude/projects", help=argparse.SUPPRESS)
    p.add_argument("--codex-root", type=Path, default=Path.home()/".codex/sessions", help=argparse.SUPPRESS)
    p.add_argument("--cursor-root", type=Path, default=Path.home()/".cursor", help=argparse.SUPPRESS)
    p.add_argument("--no-git", action="store_true", help="Disable local Git statistics")
    p.add_argument("--no-gh", action="store_true", help="Disable optional GitHub CLI statistics")
    p.add_argument("--dry-run", action="store_true", help="Print aggregate JSON without writing files")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try: period = Period.parse(args.period)
    except ValueError as exc:
        parser().error(str(exc))
    names = [name.strip() for name in args.sources.split(",") if name.strip()]
    unknown = sorted(set(names) - set(ADAPTERS))
    if unknown:
        print(f"glasshouse: unknown source(s): {', '.join(unknown)}", file=sys.stderr); return 2
    roots = {"claude_code": args.claude_root, "codex": args.codex_root, "cursor": args.cursor_root}
    results = collect_sources(names, roots, period)
    sessions = [session for result in results for session in result.sessions]
    if not sessions:
        print(f"glasshouse: no sessions found for {period.label}; choose another --period", file=sys.stderr); return 1
    metrics = compute_metrics(sessions)
    if not args.no_git:
        git = collect_git_stats([s.cwd for s in sessions], period, not args.no_gh)
        if git.commits:
            metrics.cards.append({"id":"shipped","question":"How much did you ship?","headline":f"{git.insertions:,} lines added","body":f"Across {git.commits:,} commits; {git.deletions:,} lines removed."})
        if git.commits >= 5 and git.ship_day:
            metrics.cards.append({"id":"ship_day","question":"When do you ship most?","headline":git.ship_day,"body":"Your most common commit day in this period."})
    summary = {"sessions_by_source": {r.source: len(r.sessions) for r in results}, "malformed_lines": sum(r.malformed_lines for r in results), "skipped_sources": {r.source:r.skipped for r in results if r.skipped}, "dropped_cards": metrics.dropped}
    report = {"tool":"glasshouse", "period":period.label, "cards":metrics.cards, "stats":metrics.stats, "summary":summary}
    cleaned = scrub(report); report = cleaned.value; report["summary"]["secrets_scrubbed"] = cleaned.count
    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.dry_run:
        print(payload); return 0
    html_out = args.out or Path(f"glasshouse-{period.label}.html")
    json_out = args.json_out or html_out.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True); json_out.write_text(payload + "\n", encoding="utf-8")
    render_report(report, html_out)
    print(f"Glasshouse wrote {html_out} and {json_out}")
    print(f"Parsed {len(sessions)} sessions; scrubbed {cleaned.count} sensitive value(s).")
    return 0

