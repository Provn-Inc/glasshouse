from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from .adapters import ADAPTERS, collect_sources
from .gitstats import collect_git_stats
from .metrics import compute_metrics
from .model import Period
from .outputs import OutputPaths
from .render import render_report
from .scrub import scrub
from .server import serve_report


def parser():
    p = argparse.ArgumentParser(
        prog="glasshouse",
        description="Your coding-agent work, reflected back. Private and local.",
        epilog="Preview a generated report with: glasshouse serve [REPORT.html]",
    )
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


def serve_parser():
    p = argparse.ArgumentParser(prog="glasshouse serve", description="Open a generated Glasshouse report in your browser.")
    p.add_argument("report", nargs="?", type=Path, help="Report beneath ./outputs; defaults to the newest report")
    p.add_argument("--port", type=int, default=0, help="Local port; defaults to an available port")
    p.add_argument("--no-open", action="store_true", help="Serve without opening the browser")
    return p


def _serve(argv):
    args = serve_parser().parse_args(argv)
    if not 0 <= args.port <= 65535:
        print("glasshouse serve: port must be between 0 and 65535", file=sys.stderr)
        return 2
    paths = OutputPaths()
    try:
        report = paths.report(args.report) if args.report else paths.latest_report()
        return serve_report(report, port=args.port, open_browser=not args.no_open)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"glasshouse serve: {exc}", file=sys.stderr)
        return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "serve":
        return _serve(argv[1:])
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
            body = f"Across {git.commits:,} commits; {git.deletions:,} lines removed."
            metrics.cards.append({"id":"shipped","question":"How much did you ship?","headline":f"{git.insertions:,} lines added","body":body,"detail":"These totals come from local Git numstat data within the selected calendar period. Binary changes are excluded from line totals."})
        if git.commits >= 5 and git.ship_day:
            body = "Your most common commit day in this period."
            metrics.cards.append({"id":"ship_day","question":"When do you ship most?","headline":git.ship_day,"body":body,"detail":"Glasshouse groups locally attributed commits by weekday and selects the most frequent day once at least five commits are available."})
    summary = {"sessions_by_source": {r.source: len(r.sessions) for r in results}, "malformed_lines": sum(r.malformed_lines for r in results), "skipped_sources": {r.source:r.skipped for r in results if r.skipped}, "dropped_cards": metrics.dropped}
    report = {"tool":"glasshouse", "period":period.label, "cards":metrics.cards, "stats":metrics.stats, "summary":summary}
    cleaned = scrub(report); report = cleaned.value; report["summary"]["secrets_scrubbed"] = cleaned.count
    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.dry_run:
        print(payload); return 0
    paths = OutputPaths()
    try:
        html_out = paths.resolve(args.out, f"glasshouse-{period.label}.html")
        json_out = paths.resolve(args.json_out, f"glasshouse-{period.label}.json") if args.json_out else html_out.with_suffix(".json")
    except ValueError as exc:
        print(f"glasshouse: {exc}", file=sys.stderr)
        return 2
    json_out.write_text(payload + "\n", encoding="utf-8")
    render_report(report, html_out)
    print(f"Glasshouse wrote {html_out} and {json_out}")
    print(f"Parsed {len(sessions)} sessions; scrubbed {cleaned.count} sensitive value(s).")
    return 0
