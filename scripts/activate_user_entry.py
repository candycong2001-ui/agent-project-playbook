#!/usr/bin/env python3
"""Activate the stable user-level meminit command and Codex bootstrap Skill."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Point user-level bootstrap entry files at one stable Playbook checkout."
    )
    parser.add_argument("--playbook-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument(
        "--with-global-agents",
        action="store_true",
        help="Also replace ~/.codex/AGENTS.md with the canonical thin router.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.playbook_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    source_command = root / "bin" / "meminit"
    source_skill = root / "adapters" / "codex" / "new-project-memory-bootstrap" / "SKILL.md"
    source_global_agents = root / "adapters" / "codex" / "global-AGENTS.zh-CN.md"
    required = [source_command, source_skill]
    if args.with_global_agents:
        required.append(source_global_agents)
    if any(not path.is_file() for path in required):
        parser.error(f"Playbook entry files are missing under {root}")

    command_target = home / ".local" / "bin" / "meminit"
    skill_target = home / ".agents" / "skills" / "new-project-memory-bootstrap" / "SKILL.md"
    global_agents_target = home / ".codex" / "AGENTS.md"
    mode = "apply" if args.apply else "dry-run"
    print("# User Entry Activation")
    print(f"\n- playbook_root: `{root}`")
    print(f"- mode: `{mode}`")
    print(f"- meminit: `{command_target}` -> `{source_command}`")
    print(f"- bootstrap_skill: `{skill_target}` <- `{source_skill}`")
    if args.with_global_agents:
        print(f"- global_agents: `{global_agents_target}` <- `{source_global_agents}`")

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
    if args.with_global_agents:
        global_agents_target.parent.mkdir(parents=True, exist_ok=True)
        source_text = source_global_agents.read_text(encoding="utf-8")
        if (
            global_agents_target.is_file()
            and global_agents_target.read_text(encoding="utf-8") != source_text
        ):
            stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = home / ".codex" / "backups" / f"AGENTS.md.before-playbook-{stamp}"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(global_agents_target, backup)
            print(f"- global_agents_backup: `{backup}`")
        global_agents_target.write_text(source_text, encoding="utf-8")
    print("\nActivated. The Playbook checkout is now the source for the selected user entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
