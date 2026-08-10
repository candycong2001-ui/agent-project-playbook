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
    return 0


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
        report(
            title="Init",
            root=root,
            project_name=args.project_name,
            locale=locale,
            mode=mode,
            current=[],
            created=[],
            blocked=[f"pjm init failed: {result.stdout.strip()}"],
        )
        return result.returncode

    (root / ".projectmem" / "AI_INSTRUCTIONS.md").write_text(
        instructions_template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    harden_config(root / ".projectmem" / "config.toml")
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(skill_template.read_text(encoding="utf-8"), encoding="utf-8")
    append_line_once(root / ".gitignore", IGNORE_RULES)
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
