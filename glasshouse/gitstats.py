from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import shutil, subprocess


@dataclass
class GitStats:
    commits: int = 0
    insertions: int = 0
    deletions: int = 0
    prs: int | None = None
    ship_day: str | None = None


def collect_git_stats(repos, period, include_gh=False, runner=subprocess.run):
    stats = GitStats(); days = Counter()
    if not shutil.which("git"): return stats
    for repo in sorted({Path(r) for r in repos if r and (Path(r) / ".git").exists()}):
        command = ["git", "log", f"--since={period.start.isoformat()}", f"--until={period.end.isoformat()}", "--numstat", "--format=@@%aI"]
        try: output = runner(command, cwd=repo, capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError): continue
        for line in output.splitlines():
            if line.startswith("@@"):
                stats.commits += 1
                try:
                    from datetime import datetime
                    days[datetime.fromisoformat(line[2:]).strftime("%A")] += 1
                except ValueError: pass
            else:
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    stats.insertions += int(parts[0]); stats.deletions += int(parts[1])
    if days: stats.ship_day = days.most_common(1)[0][0]
    return stats
