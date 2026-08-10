from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVATE = ROOT / "scripts" / "activate_user_entry.py"


def run(home: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ACTIVATE),
            "--playbook-root",
            str(ROOT),
            "--home",
            str(home),
            *extra,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class ActivateUserEntryTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)

            result = run(home)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- mode: `dry-run`", result.stdout)
            self.assertFalse(any(home.iterdir()))

    def test_apply_activates_meminit_and_bootstrap_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)

            result = run(home, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            command = home / ".local/bin/meminit"
            self.assertTrue(command.is_symlink())
            self.assertEqual(command.resolve(), (ROOT / "bin/meminit").resolve())
            skill = home / ".agents/skills/new-project-memory-bootstrap/SKILL.md"
            self.assertIn("name: new-project-memory-bootstrap", skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
