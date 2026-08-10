from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_safety.py"


def run(
    *arguments: str,
    cwd: Path | None = None,
    home: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if home is not None:
        environment["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git(root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return process.stdout.strip()


def initialize_repo(root: Path, branch: str = "main") -> None:
    git(root, "init", "-b", branch)
    git(root, "config", "user.email", "tester@example.com")
    git(root, "config", "user.name", "Test User")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "initial")


class ProjectSafetyTests(unittest.TestCase):
    def test_inspect_is_read_only_and_reports_current_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            initialize_repo(project)
            (project / ".agent-playbook.toml").write_text(
                'profile = "production"\n', encoding="utf-8"
            )
            skill = project / ".agents/skills/production-release-gate/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("production rules\n", encoding="utf-8")
            before = git(project, "status", "--porcelain=v1")

            result = run("inspect", str(project), "--json")

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["profile"], "production")
            self.assertTrue(payload["production_skill_installed"])
            self.assertFalse(payload["production_changed"])
            self.assertEqual(git(project, "status", "--porcelain=v1"), before)

    def test_start_dry_run_creates_nothing_and_prints_no_version_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project)

            result = run("start", str(project), "safe-task", "--json", home=root)

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(payload["branch"], "codex/safe-task")
            self.assertEqual(payload["base_ref"], "main")
            self.assertNotIn("--confirm-base", result.stdout)
            self.assertFalse((root / ".codex/worktrees/project-safe-task").exists())

    def test_start_apply_creates_worktree_without_manual_version_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            target = root / ".codex/worktrees/project-safe-task"
            project.mkdir()
            initialize_repo(project)

            result = run("start", str(project), "safe-task", "--apply", "--json", home=root)

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "created")
            self.assertEqual(git(target, "branch", "--show-current"), "codex/safe-task")
            self.assertEqual(git(project, "branch", "--show-current"), "main")

    def test_start_accepts_an_explicit_base_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project, branch="trunk")

            result = run(
                "start",
                str(project),
                "safe-task",
                "--base",
                "trunk",
                "--apply",
                "--json",
                home=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["base_ref"], "trunk")

    def test_start_rejects_an_existing_branch_or_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project)
            git(project, "branch", "codex/safe-task")

            existing_branch = run("start", str(project), "safe-task", home=root)
            self.assertEqual(existing_branch.returncode, 3, existing_branch.stdout)
            self.assertIn("task branch already exists", existing_branch.stdout)

            target = root / ".codex/worktrees/project-other-task"
            target.mkdir(parents=True)
            existing_target = run("start", str(project), "other-task", home=root)
            self.assertEqual(existing_target.returncode, 3, existing_target.stdout)
            self.assertIn("worktree target already exists", existing_target.stdout)

    def test_cleanup_removes_a_registered_worktree_and_merged_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            target = root / ".codex/worktrees/project-safe-task"
            project.mkdir()
            initialize_repo(project)
            created = run("start", str(project), "safe-task", "--apply", home=root)
            self.assertEqual(created.returncode, 0, created.stdout)

            cleanup = run(
                "cleanup",
                str(project),
                "safe-task",
                "--delete-branch",
                "--apply",
                "--json",
                home=root,
            )

            self.assertEqual(cleanup.returncode, 0, cleanup.stdout)
            self.assertFalse(target.exists())
            self.assertNotIn("codex/safe-task", git(project, "branch", "--list"))

    def test_cleanup_refuses_unregistered_target_and_unmerged_branch_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            target = root / ".codex/worktrees/project-safe-task"
            project.mkdir()
            initialize_repo(project)
            target.mkdir(parents=True)

            unregistered = run("cleanup", str(project), "safe-task", home=root)
            self.assertEqual(unregistered.returncode, 3, unregistered.stdout)
            self.assertIn("not registered", unregistered.stdout)

            target.rmdir()
            created = run("start", str(project), "safe-task", "--apply", home=root)
            self.assertEqual(created.returncode, 0, created.stdout)
            (target / "change.txt").write_text("change\n", encoding="utf-8")
            git(target, "add", "change.txt")
            git(target, "commit", "-m", "unmerged")

            unmerged = run(
                "cleanup",
                str(project),
                "safe-task",
                "--delete-branch",
                "--apply",
                home=root,
            )
            self.assertEqual(unmerged.returncode, 3, unmerged.stdout)
            self.assertIn("not merged", unmerged.stdout)
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
