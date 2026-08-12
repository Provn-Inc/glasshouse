from __future__ import annotations

from pathlib import Path


class OutputPaths:
    """Owns Glasshouse's generated-artifact boundary."""

    def __init__(self, workspace: Path | str | None = None):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.root = self.workspace / "outputs"
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, candidate: Path | str | None, default_name: str) -> Path:
        raw = Path(candidate) if candidate is not None else Path(default_name)
        if raw.is_absolute():
            raise ValueError("output paths must be relative to ./outputs")
        parts = raw.parts
        if parts and parts[0] == "outputs":
            raw = Path(*parts[1:])
        resolved = (self.root / raw).resolve()
        if resolved == self.root or self.root not in resolved.parents:
            raise ValueError("output path cannot escape ./outputs")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def report(self, candidate: Path | str) -> Path:
        report = self.resolve(candidate, "unused.html")
        if report.suffix.lower() != ".html":
            raise ValueError("report must be an .html file")
        if not report.is_file():
            raise FileNotFoundError(report)
        return report

    def latest_report(self) -> Path:
        reports = list(self.root.glob("glasshouse-*.html"))
        if not reports:
            raise FileNotFoundError("no glasshouse-*.html reports found in ./outputs")
        return max(reports, key=lambda path: path.stat().st_mtime_ns)

