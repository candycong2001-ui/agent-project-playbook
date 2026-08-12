#!/usr/bin/env python3
"""Install or inspect an Agent Project Playbook distribution."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SOURCE_ROOT / "templates"
CONTRACT = json.loads((SOURCE_ROOT / "playbook_contract.json").read_text(encoding="utf-8"))
PLAYBOOK_VERSION = str(CONTRACT["playbook_version"])
INSTALLED_SCHEMA_VERSION = int(CONTRACT["installed_schema_version"])
SUPPORTED_LOCALES = tuple(CONTRACT["supported_locales"])
DEFAULT_LOCALE = str(CONTRACT["defaults"]["locale"])
DEFAULT_PROFILE = str(CONTRACT["defaults"]["profile"])
PROFILE_DESTINATIONS = {
    profile: tuple(Path(relative) for relative in settings["destinations"])
    for profile, settings in CONTRACT["profiles"].items()
}
UPGRADE_CONTRACT = CONTRACT["upgrade"]
METADATA_DESTINATION = Path(UPGRADE_CONTRACT["metadata"])
MANAGED_DESTINATIONS = tuple(Path(relative) for relative in UPGRADE_CONTRACT["managed"])
SEEDED_DESTINATIONS = tuple(Path(relative) for relative in UPGRADE_CONTRACT["seeded"])
SUPPORTED_UPGRADE_SOURCES = tuple(str(version) for version in UPGRADE_CONTRACT["supported_from"])

SIMPLE_DESTINATIONS = PROFILE_DESTINATIONS["simple"]
PRODUCTION_DESTINATIONS = tuple(
    relative
    for relative in PROFILE_DESTINATIONS["production"]
    if relative not in SIMPLE_DESTINATIONS
)
DESTINATIONS = SIMPLE_DESTINATIONS


@dataclass(frozen=True)
class UpgradeWrite:
    relative: Path
    before: bytes | None
    after: bytes
    mode: int


@dataclass
class UpgradeActions:
    current: list[str] = field(default_factory=list)
    will_update: list[str] = field(default_factory=list)
    will_create: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    writes: list[UpgradeWrite] = field(default_factory=list)


def profile_destinations(profile: str) -> tuple[Path, ...]:
    try:
        return PROFILE_DESTINATIONS[profile]
    except KeyError as error:
        raise ValueError(f"unknown profile: {profile}") from error


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


def render(
    template: Path,
    project_name: str,
    locale: str,
    profile: str,
    projectmem: str = "disabled",
) -> str:
    return (
        template.read_text(encoding="utf-8")
        .replace("{{SCHEMA_VERSION}}", str(INSTALLED_SCHEMA_VERSION))
        .replace("{{PROJECT_NAME}}", project_name)
        .replace("{{PLAYBOOK_VERSION}}", PLAYBOOK_VERSION)
        .replace("{{PROFILE}}", profile)
        .replace("{{LOCALE}}", locale)
        .replace("{{PROJECTMEM}}", projectmem)
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


def parse_installed_metadata(
    project_root: Path,
) -> tuple[bytes | None, dict[str, str], list[str]]:
    metadata = project_root / METADATA_DESTINATION
    if not os.path.lexists(metadata):
        return (
            None,
            {},
            [".agent-playbook.toml is missing; legacy installs require manual adoption"],
        )
    if metadata.is_symlink() or not metadata.is_file():
        return None, {}, [".agent-playbook.toml is not a regular file"]
    try:
        content = metadata.read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeError) as error:
        return None, {}, [f"cannot read .agent-playbook.toml: {error}"]

    settings: dict[str, str] = {}
    errors: list[str] = []
    patterns = {
        "schema_version": r"^\s*schema_version\s*=\s*(?P<value>\d+)\s*$",
        "playbook_version": r'^\s*playbook_version\s*=\s*"(?P<value>[^"]+)"\s*$',
        "profile": r'^\s*profile\s*=\s*"(?P<value>[^"]+)"\s*$',
        "locale": r'^\s*locale\s*=\s*"(?P<value>[^"]+)"\s*$',
        "projectmem": r'^\s*projectmem\s*=\s*"(?P<value>[^"]+)"\s*$',
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.MULTILINE)
        required = key != "projectmem"
        if len(matches) == 1:
            settings[key] = matches[0]
        elif required or len(matches) > 1:
            errors.append(f".agent-playbook.toml must contain exactly one {key}")
    if settings.get("projectmem") not in {None, "disabled", "enabled"}:
        errors.append(".agent-playbook.toml projectmem must be disabled or enabled")
    return content, settings, errors


def replace_metadata_setting(text: str, key: str, value: str, *, quoted: bool) -> str:
    rendered = f'{key} = "{value}"' if quoted else f"{key} = {value}"
    pattern = rf"^\s*{re.escape(key)}\s*=.*$"
    updated, count = re.subn(pattern, rendered, text, count=1, flags=re.MULTILINE)
    if count:
        return updated
    prefix = updated.rstrip()
    return f"{prefix}\n{rendered}\n" if prefix else f"{rendered}\n"


def projectmem_state(project_root: Path, settings: dict[str, str]) -> str:
    configured = settings.get("projectmem")
    if configured is not None:
        return configured
    installed = (project_root / ".projectmem").is_dir() and (
        project_root / ".agents" / "skills" / "project-memory" / "SKILL.md"
    ).is_file()
    return "enabled" if installed else "disabled"


def upgraded_metadata(
    before: bytes,
    project_root: Path,
    settings: dict[str, str],
) -> bytes:
    text = before.decode("utf-8")
    text = replace_metadata_setting(
        text,
        "schema_version",
        str(INSTALLED_SCHEMA_VERSION),
        quoted=False,
    )
    text = replace_metadata_setting(text, "playbook_version", PLAYBOOK_VERSION, quoted=True)
    text = replace_metadata_setting(
        text,
        "projectmem",
        projectmem_state(project_root, settings),
        quoted=True,
    )
    return text.encode("utf-8")


def detected_locale(project_root: Path) -> str | None:
    agents = project_root / "AGENTS.md"
    if not agents.is_file():
        return None
    return "zh-CN" if "## 真值顺序" in agents.read_text(encoding="utf-8") else "en"


def is_within(root: Path, path: Path) -> bool:
    return path == root or root in path.parents


def validate_destination(project_root: Path, relative: Path) -> Path:
    resolved_root = project_root.resolve()
    destination = resolved_root / relative
    cursor = resolved_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symbolic link is not allowed in target path: {relative}")
        if cursor.exists() and not is_within(resolved_root, cursor.resolve()):
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


def target_mode(relative: Path) -> int:
    return 0o755 if relative.name in {"docs_lint.py", "project_safety.py"} else 0o644


def build_upgrade_actions(
    project_root: Path,
    project_name: str,
    locale: str,
    profile: str,
    files: dict[Path, Path],
) -> UpgradeActions:
    actions = UpgradeActions()
    metadata_before, settings, metadata_errors = parse_installed_metadata(project_root)
    actions.blocked.extend(metadata_errors)

    for relative in SEEDED_DESTINATIONS:
        if relative not in files:
            continue
        try:
            destination = validate_destination(project_root, relative)
        except ValueError as error:
            actions.blocked.append(str(error))
            continue
        if not os.path.lexists(destination):
            actions.preserved.append(f"{relative} is missing; restore project content manually")
        elif not destination.is_file():
            actions.blocked.append(f"{relative} is not a regular file")
        else:
            actions.preserved.append(str(relative))

    if metadata_before is None or metadata_errors:
        return actions

    source_version = settings["playbook_version"]
    try:
        source_schema = int(settings["schema_version"])
    except ValueError:
        actions.blocked.append(".agent-playbook.toml schema_version is not an integer")
        return actions
    if source_schema != INSTALLED_SCHEMA_VERSION:
        actions.blocked.append(
            f"schema_version {source_schema} is unsupported; expected {INSTALLED_SCHEMA_VERSION}"
        )
    if settings["locale"] != locale:
        actions.blocked.append(
            f"locale change is not part of safe upgrade: {settings['locale']} -> {locale}"
        )
    if settings["profile"] != profile:
        actions.blocked.append(
            f"profile change is not part of safe upgrade: {settings['profile']} -> {profile}"
        )
    if actions.blocked:
        return actions

    if source_version != PLAYBOOK_VERSION and source_version not in SUPPORTED_UPGRADE_SOURCES:
        actions.blocked.append(
            f"playbook_version {source_version} is not supported; migrate manually"
        )
        return actions

    for relative in MANAGED_DESTINATIONS:
        template = files.get(relative)
        if template is None:
            continue
        try:
            destination = validate_destination(project_root, relative)
            target = render(template, project_name, locale, profile).encode("utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            actions.blocked.append(f"{relative}: {error}")
            continue
        if not os.path.lexists(destination):
            actions.will_create.append(str(relative))
            actions.writes.append(
                UpgradeWrite(
                    relative=relative, before=None, after=target, mode=target_mode(relative)
                )
            )
            continue
        if not destination.is_file():
            actions.blocked.append(f"{relative} is not a regular file")
            continue
        try:
            current = destination.read_bytes()
        except OSError as error:
            actions.blocked.append(f"cannot read {relative}: {error}")
            continue
        if current == target:
            actions.current.append(str(relative))
            continue
        actions.blocked.append(f"{relative} is a modified managed file")

    metadata_after = upgraded_metadata(metadata_before, project_root, settings)
    if metadata_after == metadata_before:
        actions.current.append(str(METADATA_DESTINATION))
    else:
        actions.will_update.append(
            f"{METADATA_DESTINATION} ({source_version} -> {PLAYBOOK_VERSION})"
        )
        metadata_mode = (project_root / METADATA_DESTINATION).stat().st_mode & 0o777
        actions.writes.append(
            UpgradeWrite(
                relative=METADATA_DESTINATION,
                before=metadata_before,
                after=metadata_after,
                mode=metadata_mode,
            )
        )
    return actions


def read_upgrade_target(project_root: Path, relative: Path) -> tuple[bytes, int]:
    destination = validate_destination(project_root, relative)
    if not destination.is_file():
        raise FileNotFoundError(relative)
    return destination.read_bytes(), destination.stat().st_mode & 0o777


def atomic_replace(project_root: Path, relative: Path, content: bytes, mode: int) -> None:
    destination = validate_destination(project_root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".agent-playbook-upgrade-", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def apply_upgrade(project_root: Path, writes: list[UpgradeWrite]) -> str | None:
    applied: list[tuple[UpgradeWrite, int | None]] = []
    try:
        for write in writes:
            if write.before is None:
                try:
                    read_upgrade_target(project_root, write.relative)
                except FileNotFoundError:
                    pass
                else:
                    raise OSError(f"{write.relative} changed after preflight")
                old_mode = None
            else:
                current, old_mode = read_upgrade_target(project_root, write.relative)
                if current != write.before:
                    raise OSError(f"{write.relative} changed after preflight")
            atomic_replace(project_root, write.relative, write.after, write.mode)
            applied.append((write, old_mode))
    except (OSError, ValueError) as error:
        rollback_errors: list[str] = []
        for write, old_mode in reversed(applied):
            try:
                current, _ = read_upgrade_target(project_root, write.relative)
                if current != write.after:
                    raise OSError("content changed before rollback")
                if write.before is None:
                    validate_destination(project_root, write.relative).unlink()
                else:
                    atomic_replace(
                        project_root,
                        write.relative,
                        write.before,
                        old_mode or 0o644,
                    )
            except OSError as rollback_error:
                rollback_errors.append(f"{write.relative}: {rollback_error}")
        message = str(error)
        if rollback_errors:
            message += f"; rollback incomplete: {'; '.join(rollback_errors)}"
        return message
    return None


def upgrade_plan(
    project_root: Path,
    project_name: str,
    locale: str,
    profile: str,
    files: dict[Path, Path],
    *,
    apply: bool,
) -> int:
    actions = build_upgrade_actions(project_root, project_name, locale, profile, files)
    print_report(
        title="Upgrade Plan",
        project_root=project_root,
        project_name=project_name,
        locale=locale,
        profile=profile,
        mode="apply" if apply else "read-only",
        sections=(
            ("Current", actions.current),
            ("Will update", actions.will_update),
            ("Will create", actions.will_create),
            ("Preserved project content", actions.preserved),
            ("Blocked", actions.blocked),
        ),
    )
    print()
    if actions.blocked:
        print("No files were written. Resolve every blocked managed file before retrying.")
        return 3
    if not apply:
        print("No files were written. Rerun with `--upgrade --apply` to apply this plan.")
        return 0
    error = apply_upgrade(project_root, actions.writes)
    if error is not None:
        print(f"Upgrade failed and applied writes were rolled back: {error}")
        return 4
    if actions.writes:
        print("Safe upgrade applied.")
    else:
        print("No upgrade writes were needed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install project collaboration rules with a dry-run first."
    )
    parser.add_argument("project_root", help="Existing project directory")
    parser.add_argument("--project-name", help="Project name; defaults to directory name")
    parser.add_argument(
        "--locale",
        choices=SUPPORTED_LOCALES,
        help="Generated document language; defaults to installed metadata or contract default",
    )
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILE_DESTINATIONS),
        help="Distribution profile; defaults to installed metadata or contract default",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Plan a safe managed-file upgrade for an existing installation.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply a fresh install or a conflict-free --upgrade plan.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        parser.error(f"project directory does not exist: {project_root}")

    project_name = args.project_name or project_root.name
    locale = (
        args.locale
        or installed_setting(project_root, "locale")
        or detected_locale(project_root)
        or DEFAULT_LOCALE
    )
    profile = args.profile or installed_setting(project_root, "profile") or DEFAULT_PROFILE
    if locale not in SUPPORTED_LOCALES or profile not in PROFILE_DESTINATIONS:
        message = f"unsupported installed locale/profile: {locale}/{profile}"
        if args.upgrade:
            print_report(
                title="Upgrade Plan",
                project_root=project_root,
                project_name=project_name,
                locale=locale,
                profile=profile,
                mode="apply" if args.apply else "read-only",
                sections=(("Blocked", [message]),),
            )
            print("\nNo files were written.")
            return 3
        parser.error(message)
    destinations = profile_destinations(profile)
    files = template_files(locale, profile)
    if tuple(files) != destinations:
        parser.error("internal distribution order does not match the selected profile")
    missing_templates = [str(path) for path in files.values() if not path.exists()]
    if missing_templates:
        parser.error(f"repository templates are missing: {', '.join(missing_templates)}")

    if args.upgrade:
        return upgrade_plan(
            project_root,
            project_name,
            locale,
            profile,
            files,
            apply=args.apply,
        )

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
