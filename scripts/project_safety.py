#!/usr/bin/env python3
"""Inspect release isolation or safely prepare a task worktree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TASK_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,50}$")
REQUIRED_CONTRACTS = {
    "AGENTS.md": (
        "## Release isolation and environment safety",
        "## 发布隔离与环境安全",
    ),
    "docs/ARCHITECTURE.md": (
        "## Environment isolation",
        "## 环境隔离",
    ),
    "docs/CURRENT_HANDOFF.md": (
        "Production impact:",
        "生产影响：",
    ),
}


class SafetyError(RuntimeError):
    """A fail-closed project safety validation error."""


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


def default_base(root: Path) -> str:
    for candidate in ("origin/main", "main", "origin/master", "master"):
        process = subprocess.run(
            ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if process.returncode == 0:
            return candidate
    raise SafetyError("no reviewed base found; pass --base explicitly")


def contract_status(root: Path) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for relative, headings in REQUIRED_CONTRACTS.items():
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        status[relative] = any(heading in text for heading in headings)
    return status


def inspect_project(root: Path) -> dict[str, object]:
    root = git_root(root)
    contracts = contract_status(root)
    worktrees = [
        line.removeprefix("worktree ")
        for line in run_git(root, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    return {
        "status": "ok",
        "mode": "inspect",
        "project_root": str(root),
        "branch": run_git(root, "branch", "--show-current"),
        "dirty": bool(run_git(root, "status", "--porcelain=v1")),
        "worktree_count": len(worktrees),
        "contracts": contracts,
        "documentation_headings_present": all(contracts.values()),
        "physical_isolation_verified": False,
        "production_release_ready": False,
        "production_changed": False,
    }


def managed_target(root: Path, task: str) -> tuple[Path, Path]:
    home = Path.home().resolve()
    managed_root_raw = Path.home() / ".codex" / "worktrees"
    cursor = Path.home()
    for part in (Path(".codex") / "worktrees").parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise SafetyError(f"managed worktree path contains a symbolic link: {cursor}")
    managed_root = managed_root_raw.resolve()
    if (
        managed_root == home
        or managed_root == root
        or home not in managed_root.parents
        or root in managed_root.parents
    ):
        raise SafetyError(f"unsafe managed worktree root: {managed_root}")
    target = managed_root / f"{root.name}-{task}"
    if target.exists():
        raise SafetyError(f"worktree target already exists: {target}")
    return managed_root, target


def remote_branch_matches(root: Path, branch: str) -> list[str]:
    output = run_git(
        root,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/remotes",
    )
    return [line for line in output.splitlines() if line.endswith(f"/{branch}")]


def local_branch_exists(root: Path, branch: str) -> bool:
    process = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
        check=False,
    )
    return process.returncode == 0


def start_task(
    root: Path,
    *,
    task: str,
    base: str | None,
    confirm_base: str,
    apply: bool,
) -> dict[str, object]:
    root = git_root(root)
    if not TASK_SLUG.fullmatch(task):
        raise SafetyError("task must use lowercase letters, digits, and hyphens; max 51 characters")
    base_ref = base or default_base(root)
    base_commit = run_git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
    if len(base_commit) != 40:
        raise SafetyError(f"base did not resolve to a full commit SHA: {base_ref}")
    if apply and confirm_base != base_commit:
        raise SafetyError(f"base confirmation mismatch; required --confirm-base {base_commit}")
    branch = f"codex/{task}"
    if local_branch_exists(root, branch):
        raise SafetyError(f"task branch already exists: {branch}")
    remote_matches = remote_branch_matches(root, branch)
    if remote_matches:
        raise SafetyError(f"task branch already exists on a remote: {', '.join(remote_matches)}")
    managed_root, target = managed_target(root, task)
    result: dict[str, object] = {
        "status": "ready" if not apply else "created",
        "mode": "dry-run" if not apply else "apply",
        "project_root": str(root),
        "base_ref": base_ref,
        "base_commit": base_commit,
        "base_remote_freshness_verified": False,
        "required_base_confirmation": base_commit,
        "branch": branch,
        "worktree": str(target),
        "production_changed": False,
        "external_write_performed": False,
        "local_git_write_performed": bool(apply),
    }
    if not apply:
        return result
    managed_root_created = not managed_root.exists()
    managed_root.mkdir(parents=True, exist_ok=True)
    try:
        run_git(root, "branch", branch, base_ref)
        run_git(root, "worktree", "add", str(target), branch)
    except SafetyError:
        if target.is_dir() and not any(target.iterdir()):
            target.rmdir()
        registered = {
            line.removeprefix("worktree ")
            for line in run_git(root, "worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        }
        if local_branch_exists(root, branch) and str(target) not in registered:
            run_git(root, "branch", "-D", branch)
        if managed_root_created and managed_root.is_dir() and not any(managed_root.iterdir()):
            managed_root.rmdir()
        raise
    result["worktree_head"] = run_git(target, "rev-parse", "HEAD")
    return result


def build_parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Read-only isolation checks and dry-run-first worktree creation."
    )
    subparsers = value.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("project_root")
    inspect_parser.add_argument("--json", action="store_true")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("project_root")
    start_parser.add_argument("task")
    start_parser.add_argument(
        "--base",
        choices=("origin/main", "main", "origin/master", "master"),
    )
    start_parser.add_argument("--confirm-base", default="")
    start_parser.add_argument("--apply", action="store_true")
    start_parser.add_argument("--json", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    root = Path(arguments.project_root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project directory does not exist: {root}", file=sys.stderr)
        return 2
    try:
        if arguments.command == "inspect":
            result = inspect_project(root)
        else:
            result = start_task(
                root,
                task=arguments.task,
                base=arguments.base,
                confirm_base=arguments.confirm_base,
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
        if arguments.command == "start" and not arguments.apply:
            print(
                "Review the plan, then rerun with "
                f"--confirm-base {result['required_base_confirmation']} --apply."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
