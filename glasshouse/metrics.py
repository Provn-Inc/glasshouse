from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta
import re


@dataclass
class MetricResult:
    cards: list[dict]
    dropped: dict[str, str] = field(default_factory=dict)
    stats: dict = field(default_factory=dict)


def _card(card_id, question, headline, body, kind="deterministic"):
    context = {
        "archetype": "This archetype weighs your planning habits, prompt length, session pace, and use of parallel agents together. It is a descriptive best fit, not a score or fixed personality label.",
        "model_mix": "Model mix counts recorded assistant turns by model across the selected period. It reflects which model actually appeared most often in your local session history.",
        "peak_hours": "Peak hours are calculated from timestamps on typed prompts in your local timezone. Glasshouse finds the busiest rolling four-hour window, so sparse commit habits do not distort the result.",
        "plan_mode": "Planning frequency compares typed prompts recorded in plan mode with every typed prompt in the period. Tool results, system messages, and automated SDK turns are excluded.",
        "go_to_prompt": "A go-to prompt must repeat exactly after whitespace and case normalization and appear across at least three distinct sessions. One repetitive conversation cannot win this card by itself.",
        "parallel_agents": "Parallelism is the largest number of recorded session intervals that overlap. Repository count describes how widely that busiest window was distributed.",
        "prompt_length": "Prompt length uses whitespace-separated words from typed human prompts only. The headline is driven by the share below ten words, while longer context-rich prompts remain part of the distribution.",
        "cryptic_prompt": "This is selected from your shortest typed prompts, favoring messages that provide very little explicit context. It is a playful signal, not a judgment about whether the prompt worked.",
        "politeness": "Politeness counts prompts containing please, thanks, thank you, or sorry, then reports the rate per one hundred typed prompts. Repeated matches inside one prompt count once.",
        "course_change": "Course changes are approximate. Glasshouse looks for redirect language such as no, stop, actually, wait, or instead at the beginning of typed prompts and intentionally avoids false precision.",
        "longest_run": "A run is a chain of typed prompts with no gap longer than fifteen minutes. A transcript that remains open overnight is split rather than treated as one marathon session.",
        "crash_out": "This prompt has the strongest combined signal from capital letters, exclamation marks, and length. The label is intentionally playful; the report does not infer emotion beyond those visible text patterns.",
        "agent_relationship": "This reading combines planning and direction patterns to describe how you tend to collaborate. It summarizes interaction style without evaluating the quality of the work produced.",
    }.get(card_id, "This card is calculated locally from aggregate activity in the selected period. Raw transcripts are not embedded in the report.")
    return {"id": card_id, "question": question, "headline": headline, "body": body, "detail": context, "kind": kind}


def _window(hours):
    best = max(range(24), key=lambda start: sum(hours[(start + i) % 24] for i in range(4)))
    fmt = lambda h: f"{(h - 1) % 12 + 1} {'AM' if h % 24 < 12 else 'PM'}"
    return f"{fmt(best)}–{fmt((best + 4) % 24)}"


def compute_metrics(sessions) -> MetricResult:
    prompts = [p for s in sessions for p in s.prompts if p.is_typed]
    cards, dropped = [], {}
    count = len(prompts)
    if count < 10:
        return MetricResult([], {"all": "fewer than 10 typed prompts"}, {"typed_prompts": count})
    models = Counter()
    for session in sessions: models.update(session.model_counts)
    if models:
        model, turns = models.most_common(1)[0]
        cards.append(_card("model_mix", "Which model do you use most?", f"You love {model}", f"It led {turns} recorded assistant turns."))
    hours = Counter(p.ts.astimezone().hour for p in prompts)
    peak = hours.most_common(1)[0][0]
    cards.append(_card("peak_hours", "When are you most productive?", _window(hours), f"Your busiest hour starts at {peak:02d}:00 local time."))
    plan = sum(p.permission_mode == "plan" for p in prompts)
    cards.append(_card("plan_mode", "How often do you plan?", f"{round(plan / count * 100)}% in plan mode", f"{plan} of {count} typed prompts were recorded in plan mode."))
    normalized = Counter(re.sub(r"\s+", " ", p.text.strip().lower()) for p in prompts)
    repeat, times = normalized.most_common(1)[0]
    session_span = sum(any(re.sub(r"\s+", " ", p.text.strip().lower()) == repeat for p in s.prompts) for s in sessions)
    if session_span >= 3:
        cards.append(_card("go_to_prompt", "What's your go-to prompt?", f'“{repeat[:80]}”', f"It appeared in {session_span} sessions, {times} times total."))
    else: dropped["go_to_prompt"] = "repeat did not span 3 sessions"
    max_parallel = 1; repos = 1
    for start in [s.started_at for s in sessions]:
        active = [s for s in sessions if s.started_at <= start <= s.ended_at]
        if len(active) > max_parallel:
            max_parallel = len(active); repos = len({s.cwd for s in active if s.cwd})
    if max_parallel >= 2:
        cards.append(_card("parallel_agents", "How many agents do you run?", f"{max_parallel} agents in parallel", f"Your peak window covered {repos} repositories."))
    else: dropped["parallel_agents"] = "no overlapping sessions"
    short = sum(p.word_count < 10 for p in prompts)
    cards.append(_card("prompt_length", "How long are your prompts?", "Straight to the point" if short / count >= .5 else "You bring the context", f"{round(short/count*100)}% are under 10 words."))
    cryptic = min(prompts, key=lambda p: (p.word_count, len(p.text)))
    cards.append(_card("cryptic_prompt", "Your most cryptic prompt?", f'“{cryptic.text[:100]}”', "Brief, mysterious, and apparently sufficient.", "judgment"))
    polite = sum(bool(re.search(r"\b(please|thanks?|sorry)\b", p.text, re.I)) for p in prompts)
    cards.append(_card("politeness", "How polite are you to your agent?", "You thank all the time" if polite/count >= .2 else "Business first", f"{polite/count*100:.1f} polite prompts per 100."))
    redirects = sum(bool(re.match(r"\s*(no|stop|actually|wait|instead)\b", p.text, re.I)) for p in prompts)
    cards.append(_card("course_change", "How often do you change course?", "You steer, hard" if redirects else "Steady hands", f"About {round(redirects/count*10)} in 10 prompts redirect the work."))
    runs = []
    for session in sessions:
        timestamps = sorted(p.ts for p in session.prompts if p.is_typed)
        if not timestamps:
            continue
        run_start = previous = timestamps[0]
        for timestamp in timestamps[1:]:
            if timestamp - previous > timedelta(minutes=15):
                runs.append(previous - run_start)
                run_start = timestamp
            previous = timestamp
        runs.append(previous - run_start)
    longest = max(runs, default=timedelta())
    minutes = int(longest.total_seconds() // 60)
    label = f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"
    cards.append(_card("longest_run", "What's your longest agent run?", label, "Your longest recorded contiguous session."))
    crash = max(prompts, key=lambda p: (sum(c.isupper() for c in p.text), p.text.count("!"), p.word_count))
    cards.append(_card("crash_out", "What's your biggest crash out?", f'“{crash.text[:100]}”', "The prompt with the strongest all-caps and exclamation signal.", "judgment"))
    tool_counts = Counter()
    for s in sessions: tool_counts.update(s.tool_calls)
    archetype = "The Conductor" if max_parallel > 2 else "The Architect" if plan/count > .3 else "The Sprinter" if short/count > .7 else "The Craftsperson"
    cards.insert(0, _card("archetype", "Which archetype are you?", archetype, "A best-fit reading of your planning, pace, and parallelism.", "judgment"))
    cards.append(_card("agent_relationship", "How do you see your agent?", "Like a design partner" if plan else "Like a fast collaborator", "Inferred from your planning and direction patterns.", "judgment"))
    return MetricResult(cards, dropped, {"typed_prompts": count, "sessions": len(sessions), "tools": dict(tool_counts)})
