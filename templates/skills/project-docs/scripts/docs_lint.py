#!/usr/bin/env python3
"""Validate the bounded project collaboration documents."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADING_CONTRACT = {
    "AGENTS.md": (
        180,
        (
            ("truth_order", "## Truth order", "## 真值顺序"),
            ("collaboration_modes", "## Collaboration modes", "## 协作模式"),
            ("design_thinking", "## Design Thinking mapping", "## Design Thinking 映射"),
            (
                "task_routing",
                "## Automatic two-level task routing",
                "## 自动两级任务路由",
            ),
            ("vertical_slice", "## Vertical slice discipline", "## 垂直切片纪律"),
            ("multi_agent", "## Multi-agent coordination", "## 多 Agent 协作"),
            ("project_rhythm", "## Project rhythm", "## 项目节奏"),
            ("risk_verification", "## Risk and verification", "## 风险与验证"),
            (
                "release_isolation",
                "## Release isolation and environment safety",
                "## 发布隔离与环境安全",
            ),
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
        220,
        (
            ("system_shape", "## System shape", "## 系统形态"),
            ("entry_points", "## Entry points", "## 入口"),
            ("command_map", "## Command map", "## 命令清单"),
            ("important_components", "## Important components", "## 重要组件"),
            ("data_flow", "## Data flow", "## 数据流"),
            ("high_risk_areas", "## High-risk areas", "## 高风险区域"),
            ("environment_isolation", "## Environment isolation", "## 环境隔离"),
            ("deployment_rollback", "## Deployment and rollback", "## 部署与回滚"),
            ("verification", "## Verification", "## 验证"),
        ),
    ),
    "docs/CURRENT_HANDOFF.md": (
        120,
        (
            ("current_goal", "## Current goal", "## 当前目标"),
            ("active_task", "## Active task framing", "## 当前问题单"),
            ("current_slice", "## Current vertical slice", "## 当前垂直切片"),
            ("role_assignment", "## Role assignment", "## 角色分配"),
            ("completed", "## Completed", "## 已完成"),
            ("verified", "## Verified", "## 已验证"),
            ("remaining", "## Remaining", "## 剩余工作"),
            ("risks_blockers", "## Risks and blockers", "## 风险与阻塞"),
            ("parking_lot", "## Parking lot", "## 停车区"),
            ("next_action", "## Next action", "## 下一步"),
        ),
    ),
}

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
            errors.append(f"too long: {relative} has {line_count} lines; limit is {line_limit}")

        actual_headings = extract_h2(text)
        for heading in required_headings:
            count = actual_headings.count(heading)
            if count == 0:
                errors.append(f"missing heading: {relative}: {heading}")
            elif count > 1:
                errors.append(f"duplicate heading: {relative}: {heading}")

        if relative == "docs/CURRENT_HANDOFF.md" and (
            "Last updated: not started" in text or "最后更新：尚未开始" in text
        ):
            warnings.append("CURRENT_HANDOFF has not been activated yet")
        if relative == "docs/ARCHITECTURE.md" and (
            "Not verified yet" in text or "尚未验证" in text
        ):
            warnings.append("ARCHITECTURE still contains unverified placeholders")
        if relative == "docs/CURRENT_HANDOFF.md" and re.search(
            r"^## (?:Session log|History|Activity log|会话日志|历史流水)\s*$",
            text,
            re.MULTILINE | re.IGNORECASE,
        ):
            errors.append("CURRENT_HANDOFF must remain current state, not an activity diary")

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
