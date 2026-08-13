from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "glasshouse"


class AgentSkillTests(unittest.TestCase):
    def test_skill_uses_spec_directory_layout(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertTrue((SKILL / "scripts" / "glasshouse").is_file())
        self.assertTrue((SKILL / "references" / "privacy.md").is_file())
        self.assertTrue((SKILL / "assets" / "glasshouse-report.png").is_file())
        frontmatter = (SKILL / "SKILL.md").read_text().split("---", 2)[1]
        self.assertIn("name: glasshouse", frontmatter)
        self.assertIn("license: MIT", frontmatter)
        self.assertIn("compatibility:", frontmatter)

    def test_launcher_preserves_project_directory_and_forwards_arguments(self):
        launcher = SKILL / "scripts" / "glasshouse"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            bin_dir = base / "bin"
            bin_dir.mkdir()
            fake_uvx = bin_dir / "uvx"
            fake_uvx.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$PWD\" \"$@\"\n",
                encoding="utf-8",
            )
            fake_uvx.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            result = subprocess.run(
                [str(launcher), "--period", "2026-08", "--no-gh"],
                cwd=base,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(
            result.stdout.splitlines(),
            [
                str(base.resolve()),
                "--from",
                "git+https://github.com/Provn-Inc/glasshouse.git",
                "glasshouse",
                "--period",
                "2026-08",
                "--no-gh",
            ],
        )


if __name__ == "__main__":
    unittest.main()
