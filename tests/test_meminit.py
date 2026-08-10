from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_projectmem_adapter import make_fake_pjm

ROOT = Path(__file__).resolve().parents[1]
MEMINIT = ROOT / "bin" / "meminit"


def run_meminit(project: Path, fake_pjm: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PJM_BIN"] = str(fake_pjm)
    environment["FAKE_PJM_ARGS"] = str(project / "pjm-args.txt")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [str(MEMINIT), str(project), "demo", *extra],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class MeminitTests(unittest.TestCase):
    def test_dry_run_is_zero_write_and_shows_confirmation_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("# meminit dry-run", result.stdout)
            self.assertIn("--apply", result.stdout)
            self.assertFalse(any(project.iterdir()))

    def test_apply_installs_playbook_and_quiet_projectmem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / ".projectmem/config.toml").is_file())
            self.assertTrue((project / ".agents/skills/project-memory/SKILL.md").is_file())
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('locale = "zh-CN"', metadata)

    def test_without_projectmem_installs_core_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--without-projectmem", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertFalse((project / ".projectmem").exists())
            self.assertFalse((project / ".agents/skills/project-memory").exists())

    def test_production_shortcut_adds_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--production", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / ".agents/skills/production-release-gate/SKILL.md").is_file())

    def test_projectmem_conflict_stops_before_core_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            (project / ".projectmem").mkdir(parents=True)
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_upgrade_uses_installed_locale_and_profile_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)
            installed = run_meminit(
                project,
                fake,
                "--locale",
                "en",
                "--production",
                "--apply",
            )
            self.assertEqual(installed.returncode, 0, installed.stdout)
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = run_meminit(project, fake, "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- locale: `en`", result.stdout)
            self.assertIn("- profile: `production`", result.stdout)
            self.assertNotIn("differs; preserve project content", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
