import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from glasshouse.model import Period, Prompt, Session
from glasshouse.adapters.claude_code import collect as collect_claude
from glasshouse.adapters.codex import collect as collect_codex
from glasshouse.adapters.cursor import collect as collect_cursor
from glasshouse.metrics import compute_metrics
from glasshouse.scrub import scrub
from glasshouse.render import render_report
from glasshouse.cli import main


UTC = timezone.utc


@contextmanager
def working_directory(path):
    import os
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class PeriodTests(unittest.TestCase):
    def test_month_and_year_boundaries(self):
        month = Period.parse("2026-08")
        self.assertTrue(month.contains(datetime(2026, 8, 31, tzinfo=UTC)))
        self.assertFalse(month.contains(datetime(2026, 9, 1, tzinfo=month.start.tzinfo)))
        year = Period.parse("2026")
        self.assertTrue(year.contains(year.start))
        with self.assertRaises(ValueError):
            Period.parse("August")


class AdapterTests(unittest.TestCase):
    def test_claude_streams_typed_prompts_and_skips_bad_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "project" / "one.jsonl"
            file.parent.mkdir()
            rows = [
                {"type":"user","timestamp":"2026-08-02T10:00:00Z","sessionId":"s1","cwd":"/tmp/repo","promptSource":"typed","permissionMode":"plan","message":{"content":"Please ship this"}},
                {"type":"assistant","timestamp":"2026-08-02T10:01:00Z","sessionId":"s1","message":{"model":"opus","usage":{"input_tokens":10,"output_tokens":4},"content":[{"type":"tool_use","name":"Read"}]}},
                {"type":"user","timestamp":"2026-08-02T10:02:00Z","sessionId":"s1","promptSource":"sdk","message":{"content":"hidden"}},
            ]
            file.write_text("\n".join(json.dumps(r) for r in rows) + "\n{bad\n")
            result = collect_claude(root, Period.parse("2026-08"))
            self.assertEqual([p.text for p in result.sessions[0].prompts], ["Please ship this"])
            self.assertEqual(result.sessions[0].model_counts, {"opus": 1})
            self.assertEqual(result.sessions[0].tool_calls, {"Read": 1})
            self.assertEqual(result.malformed_lines, 1)

    def test_codex_normalizes_event_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "2026" / "08" / "rollout.jsonl"
            file.parent.mkdir(parents=True)
            rows = [
                {"timestamp":"2026-08-03T11:00:00Z","type":"session_meta","payload":{"id":"c1","cwd":"/tmp/codex"}},
                {"timestamp":"2026-08-03T11:01:00Z","type":"event_msg","payload":{"type":"user_message","message":"fix it"}},
                {"timestamp":"2026-08-03T11:02:00Z","type":"turn_context","payload":{"model":"gpt-5","approval_policy":"never"}},
                {"timestamp":"2026-08-03T11:03:00Z","type":"response_item","payload":{"type":"function_call","name":"exec_command"}},
            ]
            file.write_text("\n".join(json.dumps(r) for r in rows))
            result = collect_codex(root, Period.parse("2026-08"))
            self.assertEqual(result.sessions[0].prompts[0].text, "fix it")
            self.assertEqual(result.sessions[0].tool_calls, {"exec_command": 1})

    def test_cursor_reads_jsonl_and_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "projects" / "p" / "agent-transcripts" / "one.jsonl"
            transcript.parent.mkdir(parents=True)
            transcript.write_text(json.dumps({"role":"user","timestamp":"2026-08-04T12:00:00Z","content":"cursor prompt","sessionId":"u1"}))
            result = collect_cursor(root, Period.parse("2026-08"))
            self.assertEqual(result.sessions[0].prompts[0].text, "cursor prompt")


def sample_sessions():
    prompts = [Prompt("please fix this", datetime(2026,8,1,10,i,tzinfo=UTC), 3, "plan" if i < 5 else None) for i in range(10)]
    return [Session("s1", "claude_code", "/tmp/repo", None, "main", prompts[0].ts, prompts[-1].ts, False, {"opus": 5}, {"plan":5}, {"Read":3}, {"input":100,"output":30}, prompts)]


class MetricAndPrivacyTests(unittest.TestCase):
    def test_metrics_compute_core_cards_and_guards(self):
        result = compute_metrics(sample_sessions())
        ids = {card["id"] for card in result.cards}
        self.assertIn("model_mix", ids)
        self.assertIn("plan_mode", ids)
        self.assertIn("prompt_length", ids)
        self.assertNotIn("parallel_agents", ids)
        self.assertEqual(next(c for c in result.cards if c["id"] == "plan_mode")["headline"], "50% in plan mode")
        self.assertTrue(all(len(card["detail"]) > len(card["body"]) for card in result.cards))

    def test_longest_run_splits_after_fifteen_minute_prompt_gap(self):
        prompts = [Prompt("work on it", datetime(2026,8,1,10,minute,tzinfo=UTC), 3) for minute in (0, 10, 20)]
        prompts += [Prompt("work on it", datetime(2026,8,1,15,minute,tzinfo=UTC), 3) for minute in (0, 5)]
        prompts += [Prompt("padding prompt", datetime(2026,8,2,10,i,tzinfo=UTC), 2) for i in range(5)]
        session = Session("s", "codex", None, None, None, prompts[0].ts, prompts[-1].ts, False, {"gpt":1}, {}, {}, {}, prompts)
        card = next(c for c in compute_metrics([session]).cards if c["id"] == "longest_run")
        self.assertEqual(card["headline"], "20m")

    def test_scrubs_secrets_paths_and_nested_values(self):
        value = {"quote":"Bearer abcdefghijklmnop sk-abcdefghijklmnopqrstuvwxyz /Users/alice/private test@example.com 10.0.0.1"}
        result = scrub(value, Path("/Users/alice"))
        text = result.value["quote"]
        self.assertNotIn("abcdefghijklmnop", text)
        self.assertIn("[api-key]", text)
        self.assertIn("~/private", text)
        self.assertGreaterEqual(result.count, 4)


class RenderAndCliTests(unittest.TestCase):
    def test_renderer_is_self_contained_deterministic_and_escaped(self):
        report = {"period":"2026-08","cards":[{"id":"archetype","question":"Which?","headline":"<Architect>","body":"Build & ship","detail":"Longer <private> reading & context."}],"summary":{}}
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.html"
            b = Path(tmp) / "b.html"
            render_report(report, a); render_report(report, b)
            html = a.read_text()
            self.assertEqual(html, b.read_text())
            self.assertIn("&lt;Architect&gt;", html)
            self.assertEqual(html.lower().count("<script>"), 1)
            self.assertNotIn("http://", html)
            self.assertEqual(html.count("https://"), 1)
            self.assertIn("@media (max-width: 700px)", html)
            self.assertIn("role=\"button\"", html)
            self.assertIn("tabindex=\"0\"", html)
            self.assertIn("<dialog", html)
            self.assertIn("aria-modal=\"true\"", html)
            self.assertIn("aria-controls=\"card-dialog\"", html)
            self.assertIn("aria-expanded=\"false\"", html)
            self.assertIn("setAttribute('aria-expanded', 'true')", html)
            self.assertIn("Longer &lt;private&gt; reading &amp; context.", html)
            self.assertIn("@keyframes card-wiggle", html)
            self.assertNotIn('<pattern', html)
            self.assertIn('data-texture-seed=', html)
            self.assertIn('ResizeObserver', html)
            self.assertIn('renderTexture', html)
            self.assertIn('.modal-art .texture{position:absolute;inset:0;', html)
            self.assertNotIn('class="texture" viewBox=', html)
            self.assertIn("(hover:hover) and (pointer:fine)", html)
            self.assertIn("prefers-reduced-motion:reduce", html)
            self.assertIn("data-action=\"previous\"", html)
            self.assertIn("data-action=\"next\"", html)
            self.assertIn("history.replaceState", html)
            self.assertIn("lastTrigger.focus()", html)
            self.assertIn('class="provn-watermark"', html)
            self.assertIn('href="https://provn.co/?utm_source=glasshouse&amp;utm_medium=referral&amp;utm_campaign=free_tool&amp;utm_content=report_watermark"', html)
            self.assertIn('data:image/png;base64,', html)
            self.assertIn('Powered by', html)
            self.assertNotIn('https://provn.co/logo.png', html)

    def test_cli_end_to_end_with_isolated_claude_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "claude" / "project" / "session.jsonl"
            source.parent.mkdir(parents=True)
            rows = []
            for i in range(10):
                rows.append({"type":"user","timestamp":f"2026-08-02T10:{i:02d}:00Z","sessionId":"s1","cwd":str(base),"promptSource":"typed","message":{"content":"please build glasshouse"}})
            source.write_text("\n".join(json.dumps(r) for r in rows))
            with working_directory(base):
                code = main(["--period","2026-08","--sources","claude_code","--claude-root",str(base / "claude"),"--no-git"])
            out = base / "outputs" / "glasshouse-2026-08.html"
            data = base / "outputs" / "glasshouse-2026-08.json"
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            self.assertEqual(json.loads(data.read_text())["summary"]["sessions_by_source"]["claude_code"], 1)

    def test_serve_dispatches_newest_report_without_collecting(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output = base / "outputs"; output.mkdir()
            report = output / "glasshouse-2026-08.html"; report.write_text("report")
            with working_directory(base), patch("glasshouse.cli.serve_report", return_value=0) as serve, patch("glasshouse.cli.collect_sources") as collect:
                code = main(["serve", "--no-open"])
            self.assertEqual(code, 0)
            serve.assert_called_once_with(report.resolve(), port=0, open_browser=False)
            collect.assert_not_called()

    def test_generation_rejects_output_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "claude" / "session.jsonl"; source.parent.mkdir()
            rows = [{"type":"user","timestamp":f"2026-08-02T10:{i:02d}:00Z","sessionId":"s","promptSource":"typed","message":{"content":"build it now"}} for i in range(10)]
            source.write_text("\n".join(json.dumps(row) for row in rows))
            escaped_name = f"escape-{base.name}.html"
            with working_directory(base):
                code = main(["--period","2026-08","--sources","claude_code","--claude-root",str(base / "claude"),"--no-git","--out",f"../{escaped_name}"])
            self.assertEqual(code, 2)
            self.assertFalse((base.parent / escaped_name).exists())


if __name__ == "__main__":
    unittest.main()
