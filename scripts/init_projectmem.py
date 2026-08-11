#!/usr/bin/env python3
"""Install the optional quiet projectmem adapter into one fresh project."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = SOURCE_ROOT / "adapters" / "projectmem"
PJM_INIT_FLAGS = (
    "--no-hooks",
    "--no-global",
    "--no-watch",
    "--no-backfill",
    "--no-claude-md",
    "--no-stack-detect",
    "--no-mcp-config",
)
IGNORE_RULES = (
    ".projectmem/events.jsonl",
    ".projectmem/watch.pid",
    ".projectmem/watch.log",
    ".projectmem/*.db",
    ".projectmem/*.db-wal",
    ".projectmem/*.db-shm",
    ".projectmem/viz.html",
)


def pjm_binary() -> Path | None:
    configured = os.environ.get("PJM_BIN")
    discovered = configured or shutil.which("pjm")
    if not discovered:
        return None
    path = Path(discovered).expanduser().resolve()
    return path if path.is_file() and os.access(path, os.X_OK) else None


def templates(locale: str) -> tuple[Path, Path]:
    root = ADAPTER_ROOT / "templates" / locale
    return root / "AI_INSTRUCTIONS.md", root / "skills" / "project-memory" / "SKILL.md"


def detected_locale(root: Path) -> str:
    metadata = root / ".agent-playbook.toml"
    if metadata.is_file():
        match = re.search(
            r'^\s*locale\s*=\s*"(?P<locale>en|zh-CN)"\s*$',
            metadata.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if match:
            return match.group("locale")
    agents = root / "AGENTS.md"
    if agents.is_file() and "## 真值顺序" in agents.read_text(encoding="utf-8"):
        return "zh-CN"
    return "en"


def append_line_once(path: Path, lines: tuple[str, ...]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    existing_lines = existing.splitlines()
    missing = [line for line in lines if line not in existing_lines]
    if not missing:
        return
    prefix = existing.rstrip()
    content = f"{prefix}\n" if prefix else ""
    path.write_text(content + "\n".join(missing) + "\n", encoding="utf-8")


def harden_config(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "auto_capture = false" not in text.splitlines():
        path.write_text(text.rstrip() + "\nauto_capture = false\n", encoding="utf-8")


def record_projectmem_enabled(root: Path) -> None:
    metadata = root / ".agent-playbook.toml"
    if not metadata.is_file():
        return
    text = metadata.read_text(encoding="utf-8")
    rendered = 'projectmem = "enabled"'
    updated, count = re.subn(
        r"^\s*projectmem\s*=.*$",
        rendered,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if not count:
        updated = f"{updated.rstrip()}\n{rendered}\n"
    metadata.write_text(updated, encoding="utf-8")


def restore_file(path: Path, before: bytes | None) -> None:
    if path.is_symlink():
        raise OSError(f"refusing to restore through symbolic link: {path}")
    if before is None:
        path.unlink(missing_ok=True)
    else:
        path.write_bytes(before)


def remove_created_projectmem(root: Path) -> None:
    created = root / ".projectmem"
    if created.is_symlink():
        raise OSError("refusing to remove symbolic-link .projectmem after failed install")
    if created.is_dir():
        shutil.rmtree(created)
    elif os.path.lexists(created):
        created.unlink()


def remove_created_skill(skill: Path, root: Path, created: bool) -> None:
    if not created:
        return
    skill.unlink(missing_ok=True)
    current = skill.parent
    while current != root:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def report(
    *,
    title: str,
    root: Path,
    project_name: str,
    locale: str,
    mode: str,
    current: list[str],
    created: list[str],
    blocked: list[str],
) -> None:
    print(f"# Projectmem Adapter {title}")
    print()
    print(f"- project_root: `{root}`")
    print(f"- project_name: `{project_name}`")
    print(f"- locale: `{locale}`")
    print(f"- mode: `{mode}`")
    for heading, values in (("Current", current), ("Created", created), ("Blocked", blocked)):
        print(f"\n## {heading}")
        for value in values:
            print(f"- {value}")


def upgrade_plan(root: Path, project_name: str, locale: str) -> int:
    instructions_template, skill_template = templates(locale)
    expected = {
        root / ".projectmem" / "AI_INSTRUCTIONS.md": instructions_template,
        root / ".agents" / "skills" / "project-memory" / "SKILL.md": skill_template,
    }
    current: list[str] = []
    blocked: list[str] = []
    for destination, template in expected.items():
        relative = destination.relative_to(root)
        if not destination.exists():
            blocked.append(f"{relative} is missing")
        elif destination.read_text(encoding="utf-8") == template.read_text(encoding="utf-8"):
            current.append(str(relative))
        else:
            blocked.append(f"{relative} differs; preserve project content and merge manually")

    config = root / ".projectmem" / "config.toml"
    if config.is_file() and "auto_capture = false" in config.read_text(encoding="utf-8"):
        current.append(".projectmem/config.toml keeps auto capture off")
    else:
        blocked.append(".projectmem/config.toml does not confirm auto_capture = false")

    report(
        title="Upgrade Plan",
        root=root,
        project_name=project_name,
        locale=locale,
        mode="read-only",
        current=current,
        created=[],
        blocked=blocked,
    )
    print("\nNo files were written.")
    return 3 if blocked else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize quiet projectmem for one project.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--locale", choices=("en", "zh-CN"))
    parser.add_argument("--upgrade", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.upgrade and args.apply:
        parser.error("--upgrade is read-only and cannot be combined with --apply")

    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"project directory does not exist: {root}")
    locale = args.locale or detected_locale(root)
    instructions_template, skill_template = templates(locale)
    if not instructions_template.is_file() or not skill_template.is_file():
        parser.error("projectmem adapter templates are missing")
    if args.upgrade:
        return upgrade_plan(root, args.project_name, locale)

    pjm = pjm_binary()
    skill = root / ".agents" / "skills" / "project-memory" / "SKILL.md"
    blocked: list[str] = []
    if pjm is None:
        blocked.append("pjm is not executable in PATH; set PJM_BIN or install projectmem")
    if (root / ".projectmem").exists():
        blocked.append(".projectmem exists; use --upgrade and merge manually")
    if skill.exists():
        blocked.append(".agents/skills/project-memory/SKILL.md exists; merge manually")

    mode = "apply" if args.apply else "dry-run"
    planned = [
        "quiet pjm init (hooks/watch/backfill/global inheritance/MCP off)",
        ".projectmem/AI_INSTRUCTIONS.md",
        ".projectmem/config.toml: auto_capture = false",
        ".agents/skills/project-memory/SKILL.md",
        ".gitignore: projectmem runtime files",
    ]
    if blocked:
        report(
            title="Init",
            root=root,
            project_name=args.project_name,
            locale=locale,
            mode=mode,
            current=[],
            created=[],
            blocked=blocked,
        )
        print("\nNo files were written.")
        return 3
    if not args.apply:
        report(
            title="Init",
            root=root,
            project_name=args.project_name,
            locale=locale,
            mode=mode,
            current=[],
            created=[f"DRY-RUN {item}" for item in planned],
            blocked=[],
        )
        return 0

    result = subprocess.run(
        [str(pjm), "init", *PJM_INIT_FLAGS],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        cleanup_error: str | None = None
        try:
            remove_created_projectmem(root)
        except OSError as error:
            cleanup_error = str(error)
        failure = f"pjm init failed: {result.stdout.strip()}"
        if cleanup_error:
            failure += f"; cleanup incomplete: {cleanup_error}"
        report(
            title="Init",
            root=root,
            project_name=args.project_name,
            locale=locale,
            mode=mode,
            current=[],
            created=[],
            blocked=[failure],
        )
        return result.returncode

    gitignore = root / ".gitignore"
    metadata = root / ".agent-playbook.toml"
    gitignore_before = gitignore.read_bytes() if gitignore.is_file() else None
    metadata_before = metadata.read_bytes() if metadata.is_file() else None
    skill_created = False
    try:
        (root / ".projectmem" / "AI_INSTRUCTIONS.md").write_text(
            instructions_template.read_text(encoding="utf-8"), encoding="utf-8"
        )
        harden_config(root / ".projectmem" / "config.toml")
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(skill_template.read_text(encoding="utf-8"), encoding="utf-8")
        skill_created = True
        append_line_once(gitignore, IGNORE_RULES)
        record_projectmem_enabled(root)
    except (OSError, UnicodeError) as error:
        rollback_errors: list[str] = []
        for label, operation in (
            (
                "project-memory Skill",
                lambda: remove_created_skill(skill, root, skill_created),
            ),
            (".gitignore", lambda: restore_file(gitignore, gitignore_before)),
            ("metadata", lambda: restore_file(metadata, metadata_before)),
            (".projectmem", lambda: remove_created_projectmem(root)),
        ):
            try:
                operation()
            except OSError as rollback_error:
                rollback_errors.append(f"{label}: {rollback_error}")
        blocked_message = str(error)
        if rollback_errors:
            blocked_message += f"; rollback incomplete: {'; '.join(rollback_errors)}"
        report(
            title="Init",
            root=root,
            project_name=args.project_name,
            locale=locale,
            mode=mode,
            current=[],
            created=[],
            blocked=[blocked_message],
        )
        return 4
    report(
        title="Init",
        root=root,
        project_name=args.project_name,
        locale=locale,
        mode=mode,
        current=[],
        created=planned,
        blocked=[],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
