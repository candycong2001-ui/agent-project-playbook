from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.project_safety as project_safety

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_safety.py"


def run(
    *arguments: str,
    cwd: Path | None = None,
    home: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = None
    if home is not None:
        environment = os.environ.copy()
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


def initialize_repo(root: Path) -> None:
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "tester@example.com")
    git(root, "config", "user.name", "Test User")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "initial")


class ProjectSafetyTests(unittest.TestCase):
    def test_inspect_is_read_only_and_reports_missing_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            initialize_repo(project)
            before = git(project, "status", "--porcelain=v1")

            result = run("inspect", str(project), "--json")

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["documentation_headings_present"])
            self.assertFalse(payload["physical_isolation_verified"])
            self.assertFalse(payload["production_release_ready"])
            self.assertFalse(payload["production_changed"])
            self.assertEqual(git(project, "status", "--porcelain=v1"), before)

    def test_start_dry_run_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project)

            result = run(
                "start",
                str(project),
                "safe-task",
                "--json",
                home=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(payload["branch"], "codex/safe-task")
            target = root / ".codex/worktrees/project-safe-task"
            self.assertFalse(target.exists())
            self.assertNotIn("codex/safe-task", git(project, "branch", "--list"))

    def test_start_apply_creates_isolated_branch_and_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            target = root / ".codex/worktrees/project-safe-task"
            project.mkdir()
            initialize_repo(project)
            base = git(project, "rev-parse", "main")

            result = run(
                "start",
                str(project),
                "safe-task",
                "--confirm-base",
                base,
                "--apply",
                "--json",
                home=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "created")
            self.assertEqual(git(target, "branch", "--show-current"), "codex/safe-task")
            self.assertEqual(git(target, "rev-parse", "HEAD"), base)
            self.assertFalse(payload["production_changed"])
            self.assertEqual(git(project, "branch", "--show-current"), "main")

    def test_start_rejects_existing_branch_and_unsafe_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            initialize_repo(project)
            git(project, "branch", "codex/safe-task")

            existing = run("start", str(project), "safe-task", home=project.parent)
            unsafe = run(
                "start",
                str(project),
                "other-task",
                "--confirm-base",
                git(project, "rev-parse", "main"),
                "--apply",
                home=project,
            )

            self.assertEqual(existing.returncode, 3, existing.stdout)
            self.assertIn("task branch already exists", existing.stdout)
            self.assertEqual(unsafe.returncode, 3, unsafe.stdout)
            self.assertIn("unsafe managed worktree root", unsafe.stdout)

    def test_apply_requires_exact_base_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project)

            result = run(
                "start",
                str(project),
                "safe-task",
                "--apply",
                home=root,
            )

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("base confirmation mismatch", result.stdout)
            self.assertFalse((root / ".codex/worktrees/project-safe-task").exists())

    def test_start_rejects_remote_branch_and_symlinked_managed_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            initialize_repo(project)
            git(
                project,
                "update-ref",
                "refs/remotes/origin/codex/remote-task",
                "main",
            )

            remote = run(
                "start",
                str(project),
                "remote-task",
                home=root,
            )

            self.assertEqual(remote.returncode, 3, remote.stdout)
            self.assertIn("already exists on a remote", remote.stdout)

            (root / ".codex").mkdir()
            outside = root / "outside"
            outside.mkdir()
            (root / ".codex/worktrees").symlink_to(
                outside,
                target_is_directory=True,
            )
            symlinked = run(
                "start",
                str(project),
                "symlink-task",
                home=root,
            )

            self.assertEqual(symlinked.returncode, 3, symlinked.stdout)
            self.assertIn("contains a symbolic link", symlinked.stdout)

    def test_start_rejects_git_root_equal_to_managed_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            project = home / ".codex/worktrees"
            project.mkdir(parents=True)
            initialize_repo(project)

            result = run("start", str(project), "safe-task", home=home)

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("unsafe managed worktree root", result.stdout)

    def test_failed_worktree_add_removes_new_branch_and_empty_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            managed_root = Path(temporary) / "managed"
            target = managed_root / "project-safe-task"
            root.mkdir()
            branch_exists = {"value": False}

            def fake_git(_: Path, *arguments: str) -> str:
                if arguments[:2] == ("rev-parse", "--verify"):
                    return "a" * 40
                if arguments[:1] == ("branch",) and arguments[1] == "codex/safe-task":
                    branch_exists["value"] = True
                    return ""
                if arguments[:2] == ("worktree", "add"):
                    target.mkdir()
                    raise project_safety.SafetyError("simulated worktree add failure")
                if arguments[:3] == ("worktree", "list", "--porcelain"):
                    return f"worktree {root}"
                if arguments[:2] == ("branch", "-D"):
                    branch_exists["value"] = False
                    return ""
                self.fail(f"unexpected git call: {arguments}")

            with (
                mock.patch.object(project_safety, "git_root", return_value=root),
                mock.patch.object(project_safety, "run_git", side_effect=fake_git),
                mock.patch.object(
                    project_safety,
                    "local_branch_exists",
                    side_effect=lambda *_: branch_exists["value"],
                ),
                mock.patch.object(
                    project_safety,
                    "remote_branch_matches",
                    return_value=[],
                ),
                mock.patch.object(
                    project_safety,
                    "managed_target",
                    return_value=(managed_root, target),
                ),
            ):
                with self.assertRaises(project_safety.SafetyError):
                    project_safety.start_task(
                        root,
                        task="safe-task",
                        base="main",
                        confirm_base="a" * 40,
                        apply=True,
                    )

            self.assertFalse(branch_exists["value"])
            self.assertFalse(target.exists())
            self.assertFalse(managed_root.exists())

    def test_inspect_headings_do_not_claim_physical_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            initialize_repo(project)
            for relative, heading in (
                ("AGENTS.md", "## Release isolation and environment safety"),
                ("docs/ARCHITECTURE.md", "## Environment isolation\n\nNot verified"),
                ("docs/CURRENT_HANDOFF.md", "Production impact: not classified"),
            ):
                path = project / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(heading + "\n", encoding="utf-8")

            result = run("inspect", str(project), "--json")

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["documentation_headings_present"])
            self.assertFalse(payload["physical_isolation_verified"])
            self.assertFalse(payload["production_release_ready"])


if __name__ == "__main__":
    unittest.main()
