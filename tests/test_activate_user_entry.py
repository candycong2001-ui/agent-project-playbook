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

    def test_global_agents_dry_run_is_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)

            result = run(home, "--with-global-agents")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("global_agents", result.stdout)
            self.assertFalse(any(home.iterdir()))

    def test_apply_preserves_existing_global_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".codex/AGENTS.md"
            target.parent.mkdir(parents=True)
            target.write_text("old global rules\n", encoding="utf-8")

            result = run(home, "--with-global-agents", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), "old global rules\n")
            self.assertFalse((home / ".codex/backups").exists())

    def test_apply_installs_global_agents_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            result = run(home, "--with-global-agents", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            expected = (ROOT / "adapters/codex/global-AGENTS.zh-CN.md").read_text(encoding="utf-8")
            self.assertEqual((home / ".codex/AGENTS.md").read_text(encoding="utf-8"), expected)

    def test_scout_dry_run_is_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            result = run(home, "--with-reference-scout")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertFalse(any(home.iterdir()))

    def test_scout_install_preserves_personal_rules_and_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".codex/AGENTS.md"
            target.parent.mkdir()
            original = "# Personal rules\n\n## Skill 路由\n\n- user-only coordination rule\n"
            target.write_text(original, encoding="utf-8")
            result = run(home, "--with-global-agents", "--with-reference-scout", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            scout = home / ".agents/skills/reference-first-project-scout"
            self.assertTrue(scout.is_symlink())
            self.assertEqual(scout.resolve(), ROOT / "skills/reference-first-project-scout")
            self.assertTrue((scout / "references/deeper-review.md").is_file())
            after = target.read_text(encoding="utf-8")
            self.assertEqual(
                "\n".join(
                    line
                    for line in after.splitlines()
                    if "reference-first-project-scout" not in line
                )
                + "\n",
                original,
            )
            backups = list((home / ".codex/backups").glob("AGENTS.md.before-playbook-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)

            repeated = run(home, "--with-global-agents", "--with-reference-scout", "--apply")
            self.assertEqual(repeated.returncode, 0, repeated.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), after)
            self.assertEqual(
                len(list((home / ".codex/backups").glob("AGENTS.md.before-playbook-*"))), 1
            )

    def test_scout_does_not_create_global_agents_without_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            result = run(home, "--with-reference-scout", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(
                (home / ".agents/skills/reference-first-project-scout/SKILL.md").is_file()
            )
            self.assertFalse((home / ".codex").exists())

    def test_existing_scout_blocks_before_other_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            scout = home / ".agents/skills/reference-first-project-scout"
            scout.mkdir(parents=True)
            original = scout / "SKILL.md"
            original.write_text("custom scout\n", encoding="utf-8")

            result = run(home, "--with-reference-scout", "--apply")

            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertEqual(original.read_text(encoding="utf-8"), "custom scout\n")
            self.assertFalse((home / ".local").exists())
            self.assertFalse((home / ".agents/skills/new-project-memory-bootstrap").exists())


if __name__ == "__main__":
    unittest.main()
