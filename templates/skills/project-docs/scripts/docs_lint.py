#!/usr/bin/env python3
"""Validate the bounded project collaboration documents."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]

RULES = {
    "AGENTS.md": (
        180,
        (
            "## Truth order",
            "## Collaboration modes",
            "## Design Thinking mapping",
            "## Automatic two-level task routing",
            "## Vertical slice discipline",
            "## Multi-agent coordination",
            "## Project rhythm",
            "## Risk and verification",
            "## Memory boundaries",
        ),
    ),
    "docs/BLUEPRINT.md": (
        160,
        (
            "## Purpose",
            "## Users and use cases",
            "## Current outcome",
            "## Constraints and side-effect boundaries",
            "## In scope",
            "## Out of scope",
            "## Acceptance",
        ),
    ),
    "docs/ARCHITECTURE.md": (
        220,
        (
            "## System shape",
            "## Entry points",
            "## Command map",
            "## Important components",
            "## Data flow",
            "## High-risk areas",
            "## Deployment and rollback",
            "## Verification",
        ),
    ),
    "docs/CURRENT_HANDOFF.md": (
        120,
        (
            "## Current goal",
            "## Active task framing",
            "## Current vertical slice",
            "## Role assignment",
            "## Completed",
            "## Verified",
            "## Remaining",
            "## Risks and blockers",
            "## Parking lot",
            "## Next action",
        ),
    ),
}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for relative, (line_limit, headings) in RULES.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing: {relative}")
            continue

        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        if line_count > line_limit:
            errors.append(f"too long: {relative} has {line_count} lines; limit is {line_limit}")

        for heading in headings:
            count = text.count(heading)
            if count == 0:
                errors.append(f"missing heading: {relative}: {heading}")
            elif count > 1:
                errors.append(f"duplicate heading: {relative}: {heading}")

        if relative == "docs/CURRENT_HANDOFF.md" and "Last updated: not started" in text:
            warnings.append("CURRENT_HANDOFF has not been activated yet")
        if relative == "docs/ARCHITECTURE.md" and "Not verified yet" in text:
            warnings.append("ARCHITECTURE still contains unverified placeholders")
        if relative == "docs/CURRENT_HANDOFF.md" and re.search(
            r"^## (?:Session log|History|Activity log|会话日志|历史流水)\s*$",
            text,
            re.MULTILINE | re.IGNORECASE,
        ):
            errors.append("CURRENT_HANDOFF must remain current state, not an activity diary")

    print(f"Docs Lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
