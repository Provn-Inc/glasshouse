from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import calendar
import re


def parse_datetime(value: object) -> datetime | None:
    if isinstance(value, (int, float)):
        if value > 10_000_000_000:
            value /= 1000
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


@dataclass(frozen=True)
class Period:
    label: str
    start: datetime
    end: datetime

    @classmethod
    def parse(cls, value: str | None) -> "Period":
        now = datetime.now().astimezone()
        value = value or now.strftime("%Y-%m")
        if re.fullmatch(r"\d{4}-\d{2}", value):
            year, month = map(int, value.split("-"))
            if not 1 <= month <= 12:
                raise ValueError(f"invalid period: {value}")
            start = datetime(year, month, 1).astimezone()
            last = calendar.monthrange(year, month)[1]
            end = datetime(year, month, last, 23, 59, 59, 999999).astimezone()
        elif re.fullmatch(r"\d{4}", value):
            year = int(value)
            start = datetime(year, 1, 1).astimezone()
            end = datetime(year, 12, 31, 23, 59, 59, 999999).astimezone()
        else:
            raise ValueError("period must be YYYY-MM or YYYY")
        return cls(value, start, end)

    def contains(self, value: datetime) -> bool:
        if value.tzinfo is None:
            value = value.astimezone()
        return self.start <= value.astimezone() <= self.end


@dataclass
class Prompt:
    text: str
    ts: datetime
    word_count: int
    permission_mode: str | None = None
    is_typed: bool = True


@dataclass
class Session:
    id: str
    source: str
    cwd: str | None
    git_remote: str | None
    git_branch: str | None
    started_at: datetime
    ended_at: datetime
    is_sidechain: bool = False
    model_counts: dict[str, int] = field(default_factory=dict)
    permission_modes: dict[str, int] = field(default_factory=dict)
    tool_calls: dict[str, int] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    prompts: list[Prompt] = field(default_factory=list)


@dataclass
class AdapterResult:
    source: str
    sessions: list[Session] = field(default_factory=list)
    malformed_lines: int = 0
    skipped: str | None = None

