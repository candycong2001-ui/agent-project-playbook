#!/usr/bin/env python3
"""Safely install the Agent Project Playbook into one project."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SOURCE_ROOT / "templates"

DESTINATIONS = (
    Path("AGENTS.md"),
    Path("docs/BLUEPRINT.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/CURRENT_HANDOFF.md"),
    Path(".agents/skills/project-docs/SKILL.md"),
    Path(".agents/skills/project-docs/scripts/docs_lint.py"),
)


def template_files(locale: str) -> dict[Path, Path]:
    localized_root = TEMPLATE_ROOT if locale == "en" else TEMPLATE_ROOT / locale
    return {
        Path("AGENTS.md"): localized_root / "AGENTS.md",
        Path("docs/BLUEPRINT.md"): localized_root / "docs" / "BLUEPRINT.md",
        Path("docs/ARCHITECTURE.md"): localized_root / "docs" / "ARCHITECTURE.md",
        Path("docs/CURRENT_HANDOFF.md"): localized_root / "docs" / "CURRENT_HANDOFF.md",
        Path(".agents/skills/project-docs/SKILL.md"): (
            localized_root / "skills" / "project-docs" / "SKILL.md"
        ),
        Path(".agents/skills/project-docs/scripts/docs_lint.py"): (
            TEMPLATE_ROOT / "skills" / "project-docs" / "scripts" / "docs_lint.py"
        ),
    }


def render(template: Path, project_name: str) -> str:
    return template.read_text(encoding="utf-8").replace("{{PROJECT_NAME}}", project_name)


def is_within(root: Path, path: Path) -> bool:
    return path == root or root in path.parents


def validate_destination(project_root: Path, relative: Path) -> Path:
    destination = project_root / relative
    cursor = project_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symbolic link is not allowed in target path: {relative}")
        if cursor.exists() and not is_within(project_root, cursor.resolve()):
            raise ValueError(f"target path escapes project root: {relative}")
    return destination


def exclusive_write(destination: Path, content: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content)


def print_report(
    project_root: Path,
    project_name: str,
    locale: str,
    mode: str,
    created: list[str],
    blocked: list[str],
) -> None:
    print("# Agent Project Playbook Init")
    print()
    print(f"- project_root: `{project_root}`")
    print(f"- project_name: `{project_name}`")
    print(f"- locale: `{locale}`")
    print(f"- mode: `{mode}`")
    print()
    print("## Created")
    for item in created:
        print(f"- {item}")
    print()
    print("## Blocked")
    for item in blocked:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install project collaboration rules with a dry-run first."
    )
    parser.add_argument("project_root", help="Existing project directory")
    parser.add_argument("--project-name", help="Project name; defaults to directory name")
    parser.add_argument(
        "--locale",
        choices=("en", "zh-CN"),
        default="en",
        help="Generated document language; defaults to en for backward compatibility",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the full file set when no target exists. Otherwise only show the plan.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        parser.error(f"project directory does not exist: {project_root}")

    project_name = args.project_name or project_root.name
    files = template_files(args.locale)
    missing_templates = [str(path) for path in files.values() if not path.exists()]
    if missing_templates:
        parser.error(f"repository templates are missing: {', '.join(missing_templates)}")

    destinations: dict[Path, Path] = {}
    blocked: list[str] = []

    for relative in DESTINATIONS:
        try:
            destination = validate_destination(project_root, relative)
        except ValueError as error:
            blocked.append(str(error))
            continue
        destinations[relative] = destination
        if os.path.lexists(destination):
            blocked.append(f"{relative} exists; merge manually")

    mode = "apply" if args.apply else "dry-run"
    if blocked:
        print_report(project_root, project_name, args.locale, mode, [], blocked)
        print()
        print("No files were written. Merge the existing or unsafe paths manually.")
        return 3

    if not args.apply:
        created = [f"DRY-RUN {relative}" for relative in DESTINATIONS]
        print_report(project_root, project_name, args.locale, mode, created, [])
        print()
        print("Review this plan, then rerun with `--apply` to write missing files.")
        return 0

    created_paths: list[Path] = []
    try:
        for relative, template in files.items():
            destination = destinations[relative]
            destination.parent.mkdir(parents=True, exist_ok=True)
            validate_destination(project_root, relative)
            exclusive_write(destination, render(template, project_name))
            created_paths.append(destination)
            if destination.name == "docs_lint.py":
                destination.chmod(0o755)
    except (OSError, ValueError) as error:
        for path in reversed(created_paths):
            path.unlink(missing_ok=True)
        print_report(project_root, project_name, args.locale, mode, [], [str(error)])
        print()
        print("Installation stopped and files created by this run were rolled back.")
        return 4

    created = [str(relative) for relative in DESTINATIONS]
    print_report(project_root, project_name, args.locale, mode, created, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
