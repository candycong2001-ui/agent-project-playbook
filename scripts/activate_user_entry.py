#!/usr/bin/env python3
"""Activate the stable user-level meminit command and Codex bootstrap Skill."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SCOUT_NAME = "reference-first-project-scout"


def add_scout_route(existing: str, canonical: str) -> str:
    if SCOUT_NAME in existing:
        return existing
    route = next(line for line in canonical.splitlines() if f"`{SCOUT_NAME}`" in line)
    heading = "## Skill 路由\n\n"
    if heading in existing:
        return existing.replace(heading, f"{heading}{route}\n", 1)
    return f"{existing.rstrip()}\n\n## Skill 路由\n\n{route}\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Point user-level bootstrap entry files at one stable Playbook checkout."
    )
    parser.add_argument("--playbook-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument(
        "--with-global-agents",
        action="store_true",
        help="Install the canonical thin router only if ~/.codex/AGENTS.md is absent.",
    )
    parser.add_argument(
        "--with-reference-scout",
        action="store_true",
        help="Also link the reference Scout Skill and add its route to existing global AGENTS.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.playbook_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    source_command = root / "bin" / "meminit"
    source_skill = root / "adapters" / "codex" / "new-project-memory-bootstrap" / "SKILL.md"
    source_global_agents = root / "adapters" / "codex" / "global-AGENTS.zh-CN.md"
    source_scout = root / "skills" / SCOUT_NAME
    required = [source_command, source_skill]
    if args.with_global_agents or args.with_reference_scout:
        required.append(source_global_agents)
    if args.with_reference_scout:
        required.extend(
            source_scout / relative
            for relative in ("SKILL.md", "references/deeper-review.md", "agents/openai.yaml")
        )
    if any(not path.is_file() for path in required):
        parser.error(f"Playbook entry files are missing under {root}")

    command_target = home / ".local" / "bin" / "meminit"
    skill_target = home / ".agents" / "skills" / "new-project-memory-bootstrap" / "SKILL.md"
    global_agents_target = home / ".codex" / "AGENTS.md"
    scout_target = home / ".agents" / "skills" / SCOUT_NAME
    if args.with_reference_scout and os.path.lexists(scout_target):
        if not scout_target.is_symlink() or scout_target.resolve() != source_scout:
            parser.error(f"Scout destination already exists; review it manually: {scout_target}")
    if args.with_global_agents or args.with_reference_scout:
        if os.path.lexists(global_agents_target) and (
            global_agents_target.is_symlink() or not global_agents_target.is_file()
        ):
            parser.error(f"global AGENTS is not a regular file: {global_agents_target}")
    mode = "apply" if args.apply else "dry-run"
    print("# User Entry Activation")
    print(f"\n- playbook_root: `{root}`")
    print(f"- mode: `{mode}`")
    print(f"- meminit: `{command_target}` -> `{source_command}`")
    print(f"- bootstrap_skill: `{skill_target}` <- `{source_skill}`")
    if args.with_global_agents:
        print(f"- global_agents: `{global_agents_target}` <- `{source_global_agents}`")
        if global_agents_target.is_file():
            print(
                "- existing global AGENTS will be preserved; merge other template changes manually"
            )
    if args.with_reference_scout:
        print(f"- reference_scout: `{scout_target}` -> `{source_scout}`")
        print("- global route: add only the Scout trigger; preserve all existing rules")

    if not args.apply:
        print("\nNo files were written. Rerun with `--apply` after this checkout is stable.")
        return 0

    command_target.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(command_target):
        if command_target.is_dir() and not command_target.is_symlink():
            parser.error(f"cannot replace directory: {command_target}")
        command_target.unlink()
    command_target.symlink_to(source_command)

    skill_target.parent.mkdir(parents=True, exist_ok=True)
    skill_target.write_text(source_skill.read_text(encoding="utf-8"), encoding="utf-8")
    if args.with_reference_scout and not os.path.lexists(scout_target):
        scout_target.parent.mkdir(parents=True, exist_ok=True)
        scout_target.symlink_to(source_scout, target_is_directory=True)
    if args.with_global_agents or args.with_reference_scout:
        source_text = source_global_agents.read_text(encoding="utf-8")
        if global_agents_target.is_file():
            before = global_agents_target.read_text(encoding="utf-8")
            after = add_scout_route(before, source_text) if args.with_reference_scout else before
            if after != before:
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = home / ".codex" / "backups" / f"AGENTS.md.before-playbook-{stamp}"
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(global_agents_target, backup)
                global_agents_target.write_text(after, encoding="utf-8")
                print(f"- global_agents_backup: `{backup}`")
        elif args.with_global_agents:
            global_agents_target.parent.mkdir(parents=True, exist_ok=True)
            global_agents_target.write_text(source_text, encoding="utf-8")
        else:
            print("- no global AGENTS exists; Scout remains discoverable through its description")
    print("\nActivated. The Playbook checkout is now the source for the selected user entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
