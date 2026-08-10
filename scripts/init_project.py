#!/usr/bin/env python3
"""Install or inspect an Agent Project Playbook distribution."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SOURCE_ROOT / "templates"
PLAYBOOK_VERSION = "0.3.0"

SIMPLE_DESTINATIONS = (
    Path(".agent-playbook.toml"),
    Path("AGENTS.md"),
    Path("docs/BLUEPRINT.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/CURRENT_HANDOFF.md"),
    Path(".agents/skills/project-lifecycle/SKILL.md"),
    Path(".agents/skills/multi-agent-routing/SKILL.md"),
    Path(".agents/skills/project-docs/SKILL.md"),
    Path(".agents/skills/project-docs/scripts/docs_lint.py"),
)
PRODUCTION_DESTINATIONS = (
    Path(".agents/skills/production-release-gate/SKILL.md"),
    Path(".agents/skills/production-release-gate/scripts/project_safety.py"),
)
DESTINATIONS = SIMPLE_DESTINATIONS


def profile_destinations(profile: str) -> tuple[Path, ...]:
    if profile == "simple":
        return SIMPLE_DESTINATIONS
    if profile == "production":
        return SIMPLE_DESTINATIONS + PRODUCTION_DESTINATIONS
    raise ValueError(f"unknown profile: {profile}")


def template_files(locale: str, profile: str = "simple") -> dict[Path, Path]:
    localized_root = TEMPLATE_ROOT if locale == "en" else TEMPLATE_ROOT / locale
    files = {
        Path(".agent-playbook.toml"): TEMPLATE_ROOT / "agent-playbook.toml",
        Path("AGENTS.md"): localized_root / "AGENTS.md",
        Path("docs/BLUEPRINT.md"): localized_root / "docs" / "BLUEPRINT.md",
        Path("docs/ARCHITECTURE.md"): localized_root / "docs" / "ARCHITECTURE.md",
        Path("docs/CURRENT_HANDOFF.md"): localized_root / "docs" / "CURRENT_HANDOFF.md",
        Path(".agents/skills/project-lifecycle/SKILL.md"): (
            localized_root / "skills" / "project-lifecycle" / "SKILL.md"
        ),
        Path(".agents/skills/multi-agent-routing/SKILL.md"): (
            localized_root / "skills" / "multi-agent-routing" / "SKILL.md"
        ),
        Path(".agents/skills/project-docs/SKILL.md"): (
            localized_root / "skills" / "project-docs" / "SKILL.md"
        ),
        Path(".agents/skills/project-docs/scripts/docs_lint.py"): (
            TEMPLATE_ROOT / "skills" / "project-docs" / "scripts" / "docs_lint.py"
        ),
    }
    if profile == "production":
        files.update(
            {
                Path(".agents/skills/production-release-gate/SKILL.md"): (
                    localized_root / "skills" / "production-release-gate" / "SKILL.md"
                ),
                Path(".agents/skills/production-release-gate/scripts/project_safety.py"): (
                    SOURCE_ROOT / "scripts" / "project_safety.py"
                ),
            }
        )
    return files


def render(template: Path, project_name: str, locale: str, profile: str) -> str:
    return (
        template.read_text(encoding="utf-8")
        .replace("{{PROJECT_NAME}}", project_name)
        .replace("{{PLAYBOOK_VERSION}}", PLAYBOOK_VERSION)
        .replace("{{PROFILE}}", profile)
        .replace("{{LOCALE}}", locale)
    )


def installed_setting(project_root: Path, key: str) -> str | None:
    metadata = project_root / ".agent-playbook.toml"
    if not metadata.is_file():
        return None
    match = re.search(
        rf'^\s*{re.escape(key)}\s*=\s*"(?P<value>[^"]+)"\s*$',
        metadata.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return match.group("value") if match else None


def detected_locale(project_root: Path) -> str:
    agents = project_root / "AGENTS.md"
    if agents.is_file() and "## 真值顺序" in agents.read_text(encoding="utf-8"):
        return "zh-CN"
    return "en"


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
    *,
    title: str,
    project_root: Path,
    project_name: str,
    locale: str,
    profile: str,
    mode: str,
    sections: tuple[tuple[str, list[str]], ...],
) -> None:
    print(f"# Agent Project Playbook {title}")
    print()
    print(f"- playbook_version: `{PLAYBOOK_VERSION}`")
    print(f"- project_root: `{project_root}`")
    print(f"- project_name: `{project_name}`")
    print(f"- locale: `{locale}`")
    print(f"- profile: `{profile}`")
    print(f"- mode: `{mode}`")
    for heading, items in sections:
        print()
        print(f"## {heading}")
        for item in items:
            print(f"- {item}")


def upgrade_plan(
    project_root: Path,
    project_name: str,
    locale: str,
    profile: str,
    files: dict[Path, Path],
) -> int:
    current: list[str] = []
    missing: list[str] = []
    manual_merge: list[str] = []
    for relative, template in files.items():
        try:
            destination = validate_destination(project_root, relative)
        except ValueError as error:
            manual_merge.append(str(error))
            continue
        if not destination.exists():
            missing.append(str(relative))
            continue
        if not destination.is_file():
            manual_merge.append(f"{relative} is not a regular file")
            continue
        expected = render(template, project_name, locale, profile)
        if destination.read_text(encoding="utf-8") == expected:
            current.append(str(relative))
        else:
            manual_merge.append(f"{relative} differs; preserve project content and merge manually")

    print_report(
        title="Upgrade Plan",
        project_root=project_root,
        project_name=project_name,
        locale=locale,
        profile=profile,
        mode="read-only",
        sections=(
            ("Current", current),
            ("Missing", missing),
            ("Manual merge", manual_merge),
        ),
    )
    print()
    print("No files were written.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install project collaboration rules with a dry-run first."
    )
    parser.add_argument("project_root", help="Existing project directory")
    parser.add_argument("--project-name", help="Project name; defaults to directory name")
    parser.add_argument(
        "--locale",
        choices=("en", "zh-CN"),
        help="Generated document language; defaults to installed metadata or en",
    )
    parser.add_argument(
        "--profile",
        choices=("simple", "production"),
        help="Distribution profile; defaults to installed metadata or simple",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Show a read-only comparison for an existing installation.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the full file set when no target exists. Otherwise only show the plan.",
    )
    args = parser.parse_args()
    if args.upgrade and args.apply:
        parser.error("--upgrade is read-only and cannot be combined with --apply")

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        parser.error(f"project directory does not exist: {project_root}")

    project_name = args.project_name or project_root.name
    locale = (
        args.locale or installed_setting(project_root, "locale") or detected_locale(project_root)
    )
    profile = args.profile or installed_setting(project_root, "profile") or "simple"
    destinations = profile_destinations(profile)
    files = template_files(locale, profile)
    if tuple(files) != destinations:
        parser.error("internal distribution order does not match the selected profile")
    missing_templates = [str(path) for path in files.values() if not path.exists()]
    if missing_templates:
        parser.error(f"repository templates are missing: {', '.join(missing_templates)}")

    if args.upgrade:
        return upgrade_plan(project_root, project_name, locale, profile, files)

    resolved: dict[Path, Path] = {}
    blocked: list[str] = []
    for relative in destinations:
        try:
            destination = validate_destination(project_root, relative)
        except ValueError as error:
            blocked.append(str(error))
            continue
        resolved[relative] = destination
        if os.path.lexists(destination):
            blocked.append(f"{relative} exists; merge manually")

    mode = "apply" if args.apply else "dry-run"
    if blocked:
        print_report(
            title="Init",
            project_root=project_root,
            project_name=project_name,
            locale=locale,
            profile=profile,
            mode=mode,
            sections=(("Created", []), ("Blocked", blocked)),
        )
        print()
        print("No files were written. Merge existing paths manually.")
        return 3

    if not args.apply:
        created = [f"DRY-RUN {relative}" for relative in destinations]
        print_report(
            title="Init",
            project_root=project_root,
            project_name=project_name,
            locale=locale,
            profile=profile,
            mode=mode,
            sections=(("Created", created), ("Blocked", [])),
        )
        print()
        print("Review this plan, then rerun with `--apply` to write the files.")
        return 0

    created_paths: list[Path] = []
    try:
        for relative, template in files.items():
            destination = resolved[relative]
            destination.parent.mkdir(parents=True, exist_ok=True)
            validate_destination(project_root, relative)
            exclusive_write(destination, render(template, project_name, locale, profile))
            created_paths.append(destination)
            if destination.name in {"docs_lint.py", "project_safety.py"}:
                destination.chmod(0o755)
    except (OSError, UnicodeError, ValueError) as error:
        for path in reversed(created_paths):
            path.unlink(missing_ok=True)
        print_report(
            title="Init",
            project_root=project_root,
            project_name=project_name,
            locale=locale,
            profile=profile,
            mode=mode,
            sections=(("Created", []), ("Blocked", [str(error)])),
        )
        print()
        print("Installation stopped and files created by this run were rolled back.")
        return 4

    print_report(
        title="Init",
        project_root=project_root,
        project_name=project_name,
        locale=locale,
        profile=profile,
        mode=mode,
        sections=(("Created", [str(relative) for relative in destinations]), ("Blocked", [])),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
