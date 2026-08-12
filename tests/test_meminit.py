from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_init_project import CURRENT_VERSION, mark_as_previous_install
from tests.test_projectmem_adapter import make_failing_pjm, make_fake_pjm

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
            self.assertNotIn("--with-projectmem", result.stdout)
            self.assertFalse(any(project.iterdir()))

    def test_default_apply_installs_core_only_even_when_pjm_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertFalse((project / ".projectmem").exists())
            self.assertFalse((project / ".agents/skills/project-memory").exists())
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('projectmem = "disabled"', metadata)

    def test_with_projectmem_installs_quiet_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_meminit(project, fake, "--with-projectmem", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / ".projectmem/config.toml").is_file())
            self.assertTrue((project / ".agents/skills/project-memory/SKILL.md").is_file())
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('locale = "zh-CN"', metadata)
            self.assertIn('projectmem = "enabled"', metadata)

    def test_with_projectmem_can_attach_to_existing_core(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)
            installed = run_meminit(project, root / "missing-pjm", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            agents_before = (project / "AGENTS.md").read_bytes()

            result = run_meminit(project, fake, "--with-projectmem", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Projectmem adapter install", result.stdout)
            self.assertNotIn("Playbook install", result.stdout)
            self.assertTrue((project / ".projectmem").is_dir())
            self.assertEqual((project / "AGENTS.md").read_bytes(), agents_before)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('projectmem = "enabled"', metadata)

    def test_default_apply_succeeds_without_pjm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()

            result = run_meminit(project, root / "missing-pjm", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertNotIn("pjm is not executable", result.stdout)

    def test_with_projectmem_requires_pjm_before_core_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()

            result = run_meminit(
                project,
                root / "missing-pjm",
                "--with-projectmem",
                "--apply",
            )

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("pjm is not executable", result.stdout)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_projectmem_runtime_failure_rolls_back_core_and_partial_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            failing = make_failing_pjm(root)

            result = run_meminit(project, failing, "--with-projectmem", "--apply")

            self.assertEqual(result.returncode, 9, result.stdout)
            self.assertIn("Core files were rolled back", result.stdout)
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertFalse((project / ".agent-playbook.toml").exists())
            self.assertFalse((project / ".projectmem").exists())
            self.assertFalse((project / ".agents").exists())

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

            result = run_meminit(project, fake, "--with-projectmem", "--apply")

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
                "--with-projectmem",
                "--apply",
            )
            self.assertEqual(installed.returncode, 0, installed.stdout)
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = run_meminit(project, root / "missing-pjm", "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- locale: `en`", result.stdout)
            self.assertIn("- profile: `production`", result.stdout)
            self.assertIn("Projectmem upgrade check", result.stdout)
            self.assertNotIn("differs; preserve project content", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_core_only_upgrade_does_not_require_projectmem_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            missing = root / "missing-pjm"
            installed = run_meminit(project, missing, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)

            result = run_meminit(project, missing, "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Projectmem upgrade check", result.stdout)

    def test_safe_upgrade_apply_keeps_enabled_projectmem_and_checks_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)
            installed = run_meminit(project, fake, "--with-projectmem", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)

            result = run_meminit(project, root / "missing-pjm", "--upgrade", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Playbook safe upgrade", result.stdout)
            self.assertIn("Safe upgrade applied", result.stdout)
            self.assertIn("Projectmem upgrade check", result.stdout)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn(f'playbook_version = "{CURRENT_VERSION}"', metadata)
            self.assertIn('projectmem = "enabled"', metadata)

    def test_adapter_drift_blocks_before_core_upgrade_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)
            installed = run_meminit(project, fake, "--with-projectmem", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            adapter_skill = project / ".agents/skills/project-memory/SKILL.md"
            adapter_skill.write_text("project customization\n", encoding="utf-8")
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = run_meminit(project, root / "missing-pjm", "--upgrade", "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("Projectmem upgrade check", result.stdout)
            self.assertNotIn("Playbook safe upgrade", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_external_projectmem_directory_does_not_opt_in_to_adapter_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            missing = root / "missing-pjm"
            installed = run_meminit(project, missing, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            (project / ".projectmem").mkdir()

            result = run_meminit(project, missing, "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Projectmem upgrade check", result.stdout)


if __name__ == "__main__":
    unittest.main()
