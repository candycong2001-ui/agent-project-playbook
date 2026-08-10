#!/usr/bin/env python3
"""Activate the stable user-level meminit command and Codex bootstrap Skill."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Point user-level bootstrap entry files at one stable Playbook checkout."
    )
    parser.add_argument("--playbook-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.playbook_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    source_command = root / "bin" / "meminit"
    source_skill = root / "adapters" / "codex" / "new-project-memory-bootstrap" / "SKILL.md"
    if not source_command.is_file() or not source_skill.is_file():
        parser.error(f"Playbook entry files are missing under {root}")

    command_target = home / ".local" / "bin" / "meminit"
    skill_target = home / ".agents" / "skills" / "new-project-memory-bootstrap" / "SKILL.md"
    mode = "apply" if args.apply else "dry-run"
    print("# User Entry Activation")
    print(f"\n- playbook_root: `{root}`")
    print(f"- mode: `{mode}`")
    print(f"- meminit: `{command_target}` -> `{source_command}`")
    print(f"- bootstrap_skill: `{skill_target}` <- `{source_skill}`")

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
    print("\nActivated. The Playbook checkout is now the source for meminit and its user Skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
