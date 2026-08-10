#!/usr/bin/env python3
"""Inspect a production-profile project or prepare one local task worktree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TASK_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,50}$")


class SafetyError(RuntimeError):
    """A project worktree validation error."""


def run_git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stdout.strip()[-2000:]
        raise SafetyError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def git_root(project_root: Path) -> Path:
    root = Path(run_git(project_root, "rev-parse", "--show-toplevel")).resolve()
    if root != project_root:
        raise SafetyError(f"project root must be the Git root: requested={project_root} git={root}")
    return root


def ref_exists(root: Path, ref: str) -> bool:
    process = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return process.returncode == 0


def default_base(root: Path) -> str:
    for candidate in ("origin/main", "main", "origin/master", "master"):
        if ref_exists(root, candidate):
            return candidate
    raise SafetyError("no usable base found; pass --base explicitly")


def installed_profile(root: Path) -> str | None:
    metadata = root / ".agent-playbook.toml"
    if not metadata.is_file():
        return None
    match = re.search(
        r'^\s*profile\s*=\s*"(?P<value>[^"]+)"\s*$',
        metadata.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return match.group("value") if match else None


def inspect_project(root: Path) -> dict[str, object]:
    root = git_root(root)
    worktrees = [
        line.removeprefix("worktree ")
        for line in run_git(root, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    production_skill = root / ".agents/skills/production-release-gate/SKILL.md"
    architecture = root / "docs/ARCHITECTURE.md"
    return {
        "status": "ok",
        "mode": "inspect",
        "project_root": str(root),
        "branch": run_git(root, "branch", "--show-current"),
        "dirty": bool(run_git(root, "status", "--porcelain=v1")),
        "worktree_count": len(worktrees),
        "profile": installed_profile(root),
        "production_skill_installed": production_skill.is_file(),
        "architecture_present": architecture.is_file(),
        "production_changed": False,
        "external_write_performed": False,
    }


def managed_target(root: Path, task: str) -> tuple[Path, Path]:
    managed_root = (Path.home() / ".codex" / "worktrees").resolve()
    target = managed_root / f"{root.name}-{task}"
    if root == managed_root or root == target:
        raise SafetyError(f"project root conflicts with managed worktree path: {root}")
    if target.exists() or target.is_symlink():
        raise SafetyError(f"worktree target already exists: {target}")
    return managed_root, target


def local_branch_exists(root: Path, branch: str) -> bool:
    process = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
        check=False,
    )
    return process.returncode == 0


def registered_worktrees(root: Path) -> set[Path]:
    return {
        Path(line.removeprefix("worktree ")).resolve()
        for line in run_git(root, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    }


def branch_is_merged_into_head(root: Path, branch: str) -> bool:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", branch, "HEAD"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return process.returncode == 0


def start_task(
    root: Path,
    *,
    task: str,
    base: str | None,
    apply: bool,
) -> dict[str, object]:
    root = git_root(root)
    if not TASK_SLUG.fullmatch(task):
        raise SafetyError("task must use lowercase letters, digits, and hyphens; max 51 characters")
    base_ref = base or default_base(root)
    if not ref_exists(root, base_ref):
        raise SafetyError(f"base does not exist: {base_ref}")
    branch = f"codex/{task}"
    if local_branch_exists(root, branch):
        raise SafetyError(f"task branch already exists: {branch}")
    managed_root, target = managed_target(root, task)
    result: dict[str, object] = {
        "status": "ready" if not apply else "created",
        "mode": "dry-run" if not apply else "apply",
        "project_root": str(root),
        "base_ref": base_ref,
        "branch": branch,
        "worktree": str(target),
        "production_changed": False,
        "external_write_performed": False,
        "local_git_write_performed": bool(apply),
    }
    if not apply:
        return result

    managed_root.mkdir(parents=True, exist_ok=True)
    run_git(root, "worktree", "add", "-b", branch, str(target), base_ref)
    return result


def cleanup_task(
    root: Path,
    *,
    task: str,
    delete_branch: bool,
    apply: bool,
) -> dict[str, object]:
    root = git_root(root)
    if not TASK_SLUG.fullmatch(task):
        raise SafetyError("task must use lowercase letters, digits, and hyphens; max 51 characters")
    branch = f"codex/{task}"
    _, target = managed_target_for_cleanup(root, task)
    registered = target.resolve() in registered_worktrees(root)
    exists = target.exists()
    branch_exists = local_branch_exists(root, branch)
    if exists and not registered:
        raise SafetyError(f"worktree target is not registered for this repository: {target}")
    merged = branch_exists and branch_is_merged_into_head(root, branch)
    if apply and delete_branch and branch_exists and not merged:
        raise SafetyError(f"task branch is not merged into current HEAD: {branch}")

    actions: list[str] = []
    if registered:
        actions.append("remove registered worktree")
    if delete_branch and branch_exists:
        actions.append("delete merged local task branch")
    result: dict[str, object] = {
        "status": "ready" if not apply else "cleaned",
        "mode": "dry-run" if not apply else "apply",
        "project_root": str(root),
        "branch": branch,
        "worktree": str(target),
        "worktree_exists": exists,
        "worktree_registered": registered,
        "branch_exists": branch_exists,
        "branch_safe_to_delete": merged,
        "cleanup_actions": actions,
        "production_changed": False,
        "external_write_performed": False,
        "local_git_write_performed": bool(apply and actions),
    }
    if not apply:
        return result
    if registered:
        run_git(root, "worktree", "remove", str(target))
    if delete_branch and branch_exists:
        run_git(root, "branch", "-d", branch)
    return result


def managed_target_for_cleanup(root: Path, task: str) -> tuple[Path, Path]:
    managed_root = (Path.home() / ".codex" / "worktrees").resolve()
    return managed_root, managed_root / f"{root.name}-{task}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a production-profile project or manage one local task worktree."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("project_root")
    inspect_parser.add_argument("--json", action="store_true")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("project_root")
    start_parser.add_argument("task")
    start_parser.add_argument("--base", metavar="REF")
    start_parser.add_argument("--apply", action="store_true")
    start_parser.add_argument("--json", action="store_true")

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("project_root")
    cleanup_parser.add_argument("task")
    cleanup_parser.add_argument("--delete-branch", action="store_true")
    cleanup_parser.add_argument("--apply", action="store_true")
    cleanup_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    root = Path(arguments.project_root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project directory does not exist: {root}", file=sys.stderr)
        return 2
    try:
        if arguments.command == "inspect":
            result = inspect_project(root)
        elif arguments.command == "start":
            result = start_task(
                root,
                task=arguments.task,
                base=arguments.base,
                apply=arguments.apply,
            )
        else:
            result = cleanup_task(
                root,
                task=arguments.task,
                delete_branch=arguments.delete_branch,
                apply=arguments.apply,
            )
    except SafetyError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 3
    if arguments.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
        if arguments.command in {"start", "cleanup"} and not arguments.apply:
            print("Review the plan, then rerun with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
