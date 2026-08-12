import os
import tempfile
import unittest
from pathlib import Path

from glasshouse.outputs import OutputPaths


class OutputPathsTests(unittest.TestCase):
    def test_creates_output_root_and_resolves_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = OutputPaths(Path(tmp))
            self.assertTrue(paths.root.is_dir())
            self.assertEqual(paths.resolve(None, "glasshouse-2026-08.html"), paths.root / "glasshouse-2026-08.html")

    def test_accepts_relative_paths_but_rejects_escape_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = OutputPaths(Path(tmp))
            self.assertEqual(paths.resolve(Path("archive/report.html"), "fallback.html"), paths.root / "archive/report.html")
            with self.assertRaises(ValueError):
                paths.resolve(Path("../report.html"), "fallback.html")
            with self.assertRaises(ValueError):
                paths.resolve(Path(tmp) / "report.html", "fallback.html")

    def test_latest_report_uses_modification_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = OutputPaths(Path(tmp))
            older = paths.root / "glasshouse-2026-07.html"
            newer = paths.root / "glasshouse-2026-08.html"
            older.write_text("old"); newer.write_text("new")
            os.utime(older, (1, 1)); os.utime(newer, (2, 2))
            self.assertEqual(paths.latest_report(), newer)

    def test_latest_report_errors_when_none_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                OutputPaths(Path(tmp)).latest_report()
