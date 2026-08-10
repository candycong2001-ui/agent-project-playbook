from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "scripts" / "init_project.py"

EXPECTED_FILES = (
    ".agent-playbook.toml",
    "AGENTS.md",
    "docs/BLUEPRINT.md",
    "docs/ARCHITECTURE.md",
    "docs/CURRENT_HANDOFF.md",
    ".agents/skills/project-lifecycle/SKILL.md",
    ".agents/skills/multi-agent-routing/SKILL.md",
    ".agents/skills/project-docs/SKILL.md",
    ".agents/skills/project-docs/scripts/docs_lint.py",
)
PRODUCTION_FILES = (
    ".agents/skills/production-release-gate/SKILL.md",
    ".agents/skills/production-release-gate/scripts/project_safety.py",
)


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def initialize(
    project: Path,
    *extra: str,
    locale: str = "en",
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            str(INITIALIZER),
            str(project),
            "--project-name",
            "demo-project",
            "--locale",
            locale,
            *extra,
        ]
    )


class InitProjectTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self) -> None:
        for locale in ("en", "zh-CN"):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                result = initialize(project, locale=locale)

                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"- locale: `{locale}`", result.stdout)
                self.assertIn("- profile: `simple`", result.stdout)
                self.assertIn("- mode: `dry-run`", result.stdout)
                self.assertFalse(any(project.iterdir()))

    def test_apply_creates_complete_playbook_and_lint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            for relative in EXPECTED_FILES:
                self.assertTrue((project / relative).exists(), relative)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('playbook_version = "0.3.0"', metadata)
            self.assertIn('profile = "simple"', metadata)

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# demo-project Working Agreement", agents)
            self.assertIn("## Skill routing", agents)
            self.assertIn("If `project-memory` is installed", agents)
            self.assertNotIn("## Design Thinking mapping", agents)
            self.assertNotIn("## Release isolation and environment safety", agents)

            for name in ("project-lifecycle", "multi-agent-routing", "project-docs"):
                skill = (project / f".agents/skills/{name}/SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(skill.startswith(f"---\nname: {name}\n"))

            handoff = (project / "docs/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("## Current state", handoff)
            self.assertIn("## Next action", handoff)
            self.assertNotIn("Role assignment", handoff)
            self.assertNotIn("Production impact:", handoff)
            self.assertFalse(
                (project / ".agents/skills/project-docs/scripts/project_safety.py").exists()
            )
            for relative in PRODUCTION_FILES:
                self.assertFalse((project / relative).exists(), relative)

            lint = run(
                [sys.executable, ".agents/skills/project-docs/scripts/docs_lint.py"],
                cwd=project,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("Docs Lint: 0 error(s)", lint.stdout)

    def test_production_profile_adds_only_production_skill_and_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--profile", "production", "--apply", locale="zh-CN")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- profile: `production`", result.stdout)
            for relative in EXPECTED_FILES + PRODUCTION_FILES:
                self.assertTrue((project / relative).exists(), relative)
            production_skill = (project / PRODUCTION_FILES[0]).read_text(encoding="utf-8")
            self.assertIn("name: production-release-gate", production_skill)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn('profile = "production"', metadata)

    def test_zh_cn_apply_creates_localized_playbook_and_lint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--apply", locale="zh-CN")

            self.assertEqual(result.returncode, 0, result.stdout)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# demo-project 项目协作约定", agents)
            self.assertIn("## Skill 路由", agents)
            self.assertIn("如果已经安装 `project-memory`", agents)
            self.assertNotIn("## Design Thinking 映射", agents)
            self.assertNotIn("## 发布隔离与环境安全", agents)

            handoff = (project / "docs/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("## 当前状态", handoff)
            self.assertIn("## 下一步", handoff)
            self.assertNotIn("## 角色分配", handoff)
            self.assertNotIn("生产影响：", handoff)

            lint = run(
                [sys.executable, ".agents/skills/project-docs/scripts/docs_lint.py"],
                cwd=project,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("Docs Lint: 0 error(s)", lint.stdout)

    def test_existing_file_blocks_the_entire_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("existing rules\n", encoding="utf-8")

            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertEqual(agents.read_text(encoding="utf-8"), "existing rules\n")
            self.assertIn("AGENTS.md exists; merge manually", result.stdout)
            self.assertFalse((project / "docs").exists())
            self.assertFalse((project / ".agents").exists())

    def test_symbolic_link_escape_is_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            outside = root / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "docs").symlink_to(outside, target_is_directory=True)

            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("symbolic link is not allowed", result.stdout)
            self.assertFalse(any(outside.iterdir()))
            self.assertFalse((project / "AGENTS.md").exists())

    def test_upgrade_is_read_only_and_reports_current_missing_and_manual_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            agents = project / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8") + "\nproject rule\n", encoding="utf-8"
            )
            missing = project / ".agents/skills/project-lifecycle/SKILL.md"
            missing.unlink()
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = initialize(project, "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- mode: `read-only`", result.stdout)
            self.assertIn(
                "AGENTS.md differs; preserve project content and merge manually", result.stdout
            )
            self.assertIn(".agents/skills/project-lifecycle/SKILL.md", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_upgrade_uses_installed_production_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--profile", "production", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)

            result = run([sys.executable, str(INITIALIZER), str(project), "--upgrade"])

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- profile: `production`", result.stdout)
            self.assertIn(".agents/skills/production-release-gate/SKILL.md", result.stdout)

    def test_upgrade_detects_legacy_chinese_project_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "AGENTS.md").write_text("# 旧项目\n\n## 真值顺序\n", encoding="utf-8")

            result = run([sys.executable, str(INITIALIZER), str(project), "--upgrade"])

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- locale: `zh-CN`", result.stdout)
            self.assertIn("- profile: `simple`", result.stdout)

    def test_upgrade_cannot_be_combined_with_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("--upgrade is read-only", result.stdout)


if __name__ == "__main__":
    unittest.main()
