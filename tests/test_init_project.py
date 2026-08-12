from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import init_project

ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "scripts" / "init_project.py"
CURRENT_VERSION = init_project.PLAYBOOK_VERSION
PREVIOUS_VERSION = "0.3.1"

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


def mark_as_previous_install(project: Path, version: str = PREVIOUS_VERSION) -> None:
    metadata = project / ".agent-playbook.toml"
    text = metadata.read_text(encoding="utf-8")
    text = re.sub(
        r'^playbook_version = "[^"]+"$',
        f'playbook_version = "{version}"',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r'^projectmem = "[^"]+"\n?', "", text, flags=re.MULTILINE)
    metadata.write_text(text, encoding="utf-8")


class InitProjectTests(unittest.TestCase):
    def test_direct_initializer_uses_contract_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = run([sys.executable, str(INITIALIZER), str(project)])

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- locale: `zh-CN`", result.stdout)
            self.assertIn("- profile: `simple`", result.stdout)
            self.assertFalse(any(project.iterdir()))

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
            self.assertIn(f'playbook_version = "{CURRENT_VERSION}"', metadata)
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

    def test_upgrade_plan_is_read_only_and_preserves_project_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
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
            self.assertIn("## Preserved project content", result.stdout)
            self.assertIn("- AGENTS.md", result.stdout)
            self.assertIn("## Will create", result.stdout)
            self.assertIn(".agents/skills/project-lifecycle/SKILL.md", result.stdout)
            self.assertIn(f"{PREVIOUS_VERSION} -> {CURRENT_VERSION}", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_upgrade_apply_updates_metadata_and_preserves_project_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            agents = project / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8") + "\nproject-owned rule\n",
                encoding="utf-8",
            )
            before_agents = agents.read_bytes()

            files = init_project.template_files("en", "simple")
            actions = init_project.build_upgrade_actions(
                project,
                "demo-project",
                "en",
                "simple",
                files,
            )

            self.assertFalse(actions.blocked, actions.blocked)
            self.assertFalse(
                any(item.startswith(".agents/skills/") for item in actions.will_update)
            )
            error = init_project.apply_upgrade(project, actions.writes)

            self.assertIsNone(error)
            self.assertEqual(agents.read_bytes(), before_agents)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn(f'playbook_version = "{CURRENT_VERSION}"', metadata)
            self.assertIn('projectmem = "disabled"', metadata)

    def test_upgrade_apply_creates_missing_managed_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            relative = Path(".agents/skills/project-lifecycle/SKILL.md")
            (project / relative).unlink()

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((project / relative).is_file())
            self.assertIn("Safe upgrade applied", result.stdout)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn(f'playbook_version = "{CURRENT_VERSION}"', metadata)

    def test_supported_source_versions_cover_both_locales(self) -> None:
        for source_version in ("0.3.0", "0.3.1"):
            for locale in ("en", "zh-CN"):
                with (
                    self.subTest(source_version=source_version, locale=locale),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    project = Path(temporary)
                    installed = initialize(project, "--apply", locale=locale)
                    self.assertEqual(installed.returncode, 0, installed.stdout)
                    mark_as_previous_install(project, source_version)

                    result = initialize(project, "--upgrade", locale=locale)

                    self.assertEqual(result.returncode, 0, result.stdout)
                    self.assertIn(f"{source_version} -> {CURRENT_VERSION}", result.stdout)

    def test_modified_managed_file_blocks_apply_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            managed = project / ".agents/skills/project-lifecycle/SKILL.md"
            managed.write_text(
                managed.read_text(encoding="utf-8") + "\nlocal customization\n",
                encoding="utf-8",
            )
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("modified managed file", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_upgrade_rolls_back_when_a_later_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            first = Path(".agents/skills/project-lifecycle/SKILL.md")
            second = Path(".agents/skills/multi-agent-routing/SKILL.md")
            (project / first).unlink()
            (project / second).unlink()
            metadata_before = (project / ".agent-playbook.toml").read_bytes()
            actions = init_project.build_upgrade_actions(
                project,
                "demo-project",
                "en",
                "simple",
                init_project.template_files("en", "simple"),
            )
            original_replace = init_project.atomic_replace

            def fail_second(
                project_root: Path,
                relative: Path,
                content: bytes,
                mode: int,
            ) -> None:
                if relative == second:
                    raise OSError("injected failure")
                original_replace(project_root, relative, content, mode)

            with mock.patch.object(init_project, "atomic_replace", side_effect=fail_second):
                error = init_project.apply_upgrade(project, actions.writes)

            self.assertIn("injected failure", error or "")
            self.assertFalse((project / first).exists())
            self.assertFalse((project / second).exists())
            self.assertEqual((project / ".agent-playbook.toml").read_bytes(), metadata_before)

    def test_upgrade_rejects_managed_symlink_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            relative = Path(".agents/skills/project-lifecycle/SKILL.md")
            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (project / relative).unlink()
            (project / relative).symlink_to(outside)
            metadata_before = (project / ".agent-playbook.toml").read_bytes()

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("symbolic link is not allowed", result.stdout)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")
            self.assertEqual((project / ".agent-playbook.toml").read_bytes(), metadata_before)

    def test_upgrade_uses_installed_production_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--profile", "production", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)

            result = run([sys.executable, str(INITIALIZER), str(project), "--upgrade", "--apply"])

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- profile: `production`", result.stdout)
            self.assertIn(".agents/skills/production-release-gate/SKILL.md", result.stdout)
            metadata = (project / ".agent-playbook.toml").read_text(encoding="utf-8")
            self.assertIn(f'playbook_version = "{CURRENT_VERSION}"', metadata)

    def test_upgrade_rejects_legacy_project_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "AGENTS.md").write_text("# 旧项目\n\n## 真值顺序\n", encoding="utf-8")

            result = run([sys.executable, str(INITIALIZER), str(project), "--upgrade"])

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("- locale: `zh-CN`", result.stdout)
            self.assertIn("- profile: `simple`", result.stdout)
            self.assertIn("legacy installs require manual adoption", result.stdout)

    def test_unknown_source_version_blocks_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project, "9.9.9")
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("is not supported", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_unknown_schema_blocks_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = initialize(project, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            mark_as_previous_install(project)
            metadata = project / ".agent-playbook.toml"
            metadata.write_text(
                metadata.read_text(encoding="utf-8").replace(
                    "schema_version = 1", "schema_version = 99"
                ),
                encoding="utf-8",
            )
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = initialize(project, "--upgrade", "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("schema_version 99 is unsupported", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
