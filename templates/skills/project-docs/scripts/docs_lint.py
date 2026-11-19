#!/usr/bin/env python3
"""Validate the bounded project collaboration documents."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADING_CONTRACT = {
    "AGENTS.md": (
        90,
        (
            ("truth_order", "## Truth order", "## 真值顺序"),
            ("working_defaults", "## Working defaults", "## 默认工作方式"),
            ("skill_routing", "## Skill routing", "## Skill 路由"),
            ("project_rhythm", "## Project rhythm", "## 项目节奏"),
            ("risk_verification", "## Risk and verification", "## 风险与验证"),
            ("memory_boundaries", "## Memory boundaries", "## 记忆边界"),
        ),
    ),
    "docs/BLUEPRINT.md": (
        160,
        (
            ("purpose", "## Purpose", "## 目的"),
            ("users_use_cases", "## Users and use cases", "## 用户与使用场景"),
            ("current_outcome", "## Current outcome", "## 当前成果"),
            (
                "constraints_side_effects",
                "## Constraints and side-effect boundaries",
                "## 约束与外部副作用边界",
            ),
            ("in_scope", "## In scope", "## 范围内"),
            ("out_of_scope", "## Out of scope", "## 范围外"),
            ("acceptance", "## Acceptance", "## 验收"),
        ),
    ),
    "docs/ARCHITECTURE.md": (
        160,
        (
            ("system_shape", "## System shape", "## 系统形态"),
            ("entry_points", "## Entry points", "## 入口"),
            ("command_map", "## Command map", "## 命令清单"),
            ("important_components", "## Important components", "## 重要组件"),
            ("data_flow", "## Data flow", "## 数据流"),
            (
                "runtime_side_effects",
                "## Runtime and side effects",
                "## 运行与外部副作用",
            ),
            ("high_risk_areas", "## High-risk areas", "## 高风险区域"),
            ("verification", "## Verification", "## 验证"),
        ),
    ),
    "docs/CURRENT_HANDOFF.md": (
        80,
        (
            ("current_goal", "## Current goal", "## 当前目标"),
            ("current_state", "## Current state", "## 当前状态"),
            ("verified", "## Verified", "## 已验证"),
            ("remaining", "## Remaining", "## 剩余工作"),
            ("risks_blockers", "## Risks and blockers", "## 风险与阻塞"),
            ("next_action", "## Next action", "## 下一步"),
        ),
    ),
}

HANDOFF_UPDATED = re.compile(r"^(?:Last updated|最后更新)[：:].+$", re.MULTILINE)
HANDOFF_ACTIVITY_HEADING = re.compile(
    r"^## (?:Session log|History|Activity log|Progress log|Deployment log|Changelog|"
    r"会话日志|历史流水|活动日志|进度日志|部署日志|变更日志)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
DATED_ACTIVITY_LINE = re.compile(
    r"^\s*(?:[-*>]\s*)?\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:[ T]\d{1,2}:\d{2})?",
    re.MULTILINE,
)

LANGUAGE_HEADING_INDEX = {"en": 1, "zh-CN": 2}
RULES = {
    language: {
        relative: (
            line_limit,
            tuple(section[index] for section in sections),
        )
        for relative, (line_limit, sections) in HEADING_CONTRACT.items()
    }
    for language, index in LANGUAGE_HEADING_INDEX.items()
}


def has_project_anchor(path: Path) -> bool:
    return (path / "AGENTS.md").is_file() and (path / "docs" / "CURRENT_HANDOFF.md").is_file()


def find_project_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        candidate = Path(explicit_root).expanduser().resolve()
        if candidate.is_dir():
            return candidate
        raise ValueError(f"project root is not an existing directory: {candidate}")

    starts = (Path(__file__).resolve().parent, Path.cwd().resolve())
    visited: set[Path] = set()
    for start in starts:
        for candidate in (start, *start.parents):
            if candidate in visited:
                continue
            visited.add(candidate)
            if has_project_anchor(candidate):
                return candidate

    raise ValueError(
        "could not locate the project root; pass --project-root or run inside a project "
        "containing AGENTS.md and docs/CURRENT_HANDOFF.md"
    )


def extract_h2(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip() for line in text.splitlines() if re.fullmatch(r"## [^#].*", line.strip())
    )


def detect_language(root: Path, explicit_language: str | None = None) -> str:
    if explicit_language:
        return explicit_language
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return "en"
    headings = extract_h2(agents.read_text(encoding="utf-8"))
    return "zh-CN" if "## 真值顺序" in headings else "en"


def lint_project(root: Path, language: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for relative, (line_limit, required_headings) in RULES[language].items():
        path = root / relative
        if not path.exists():
            errors.append(f"missing: {relative}")
            continue

        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        if line_count > line_limit:
            warnings.append(
                f"too long: {relative} has {line_count} lines; threshold is {line_limit}"
            )

        actual_headings = extract_h2(text)
        for heading in required_headings:
            count = actual_headings.count(heading)
            if count == 0:
                errors.append(f"missing heading: {relative}: {heading}")
            elif count > 1:
                errors.append(f"duplicate heading: {relative}: {heading}")

        if relative == "docs/CURRENT_HANDOFF.md":
            updated_count = len(HANDOFF_UPDATED.findall(text))
            if updated_count != 1:
                errors.append(
                    "CURRENT_HANDOFF must contain exactly one current Last updated marker"
                )
            if "Last updated: not started" in text or "最后更新：尚未开始" in text:
                warnings.append("CURRENT_HANDOFF has not been activated yet")
            if HANDOFF_ACTIVITY_HEADING.search(text):
                errors.append("CURRENT_HANDOFF must remain current state, not an activity diary")
            if len(DATED_ACTIVITY_LINE.findall(text)) >= 3:
                warnings.append(
                    "CURRENT_HANDOFF looks like a dated activity stream; replace history with current state"
                )
        if relative == "docs/ARCHITECTURE.md" and (
            "Not verified yet" in text or "尚未验证" in text
        ):
            warnings.append("ARCHITECTURE still contains unverified placeholders")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", help="Project root to lint; auto-detected by default")
    parser.add_argument("--language", choices=tuple(RULES), help="Template language")
    args = parser.parse_args(argv)

    try:
        root = find_project_root(args.project_root)
    except ValueError as error:
        print("Docs Lint: 1 error(s), 0 warning(s)")
        print(f"ERROR: {error}")
        return 2

    language = detect_language(root, args.language)
    errors, warnings = lint_project(root, language)

    print(f"Docs Lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
