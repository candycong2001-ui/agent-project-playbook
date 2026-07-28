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
    "AGENTS.md",
    "docs/BLUEPRINT.md",
    "docs/ARCHITECTURE.md",
    "docs/CURRENT_HANDOFF.md",
    ".agents/skills/project-docs/SKILL.md",
    ".agents/skills/project-docs/scripts/docs_lint.py",
    ".agents/skills/project-docs/scripts/project_safety.py",
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
                self.assertIn("- mode: `dry-run`", result.stdout)
                self.assertFalse(any(project.iterdir()))

    def test_apply_creates_complete_playbook_and_lint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            for relative in EXPECTED_FILES:
                self.assertTrue((project / relative).exists(), relative)

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# demo-project Working Agreement", agents)
            self.assertIn("## Design Thinking mapping", agents)
            self.assertIn("## Automatic two-level task routing", agents)
            self.assertIn("## Release isolation and environment safety", agents)

            skill = (project / ".agents/skills/project-docs/SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(skill.startswith("---\nname: project-docs\n"))

            handoff = (project / "docs/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("Collaboration mode:", handoff)
            self.assertIn("Project stage:", handoff)
            self.assertIn("Current deliverable:", handoff)
            self.assertIn("Role assignment", handoff)
            self.assertIn("Production impact:", handoff)

            lint = run(
                [sys.executable, ".agents/skills/project-docs/scripts/docs_lint.py"],
                cwd=project,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("Docs Lint: 0 error(s)", lint.stdout)

    def test_zh_cn_apply_creates_localized_playbook_and_lint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--apply", locale="zh-CN")

            self.assertEqual(result.returncode, 0, result.stdout)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# demo-project 项目协作约定", agents)
            self.assertIn("## Design Thinking 映射", agents)
            self.assertIn("## 自动两级任务路由", agents)
            self.assertIn("## 发布隔离与环境安全", agents)

            handoff = (project / "docs/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("协作模式：", handoff)
            self.assertIn("项目阶段：", handoff)
            self.assertIn("本轮交付物：", handoff)
            self.assertIn("## 角色分配", handoff)
            self.assertIn("生产影响：", handoff)

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


if __name__ == "__main__":
    unittest.main()
