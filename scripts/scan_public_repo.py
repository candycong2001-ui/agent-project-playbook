#!/usr/bin/env python3
"""Scan tracked public files for likely private paths and credentials."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "user home path": re.compile(r"/(?:Users|home)/[^/\s\"']+/"),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "GitHub token": re.compile(
        rf"\b(?:gh[pousr]_[A-Za-z0-9_]{{20,}}|{'github' + '_pat_'}[A-Za-z0-9_]{{20,}})"
    ),
    "API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
}
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PLACEHOLDER_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
PLACEHOLDER_EMAIL_SUFFIXES = (".example", ".test", ".invalid", ".localhost")


def is_placeholder_email_domain(domain: str) -> bool:
    normalized = domain.lower().rstrip(".")
    return (
        normalized in PLACEHOLDER_EMAIL_DOMAINS
        or any(normalized.endswith(f".{item}") for item in PLACEHOLDER_EMAIL_DOMAINS)
        or normalized.endswith(PLACEHOLDER_EMAIL_SUFFIXES)
    )


def scan_text(text: str) -> list[str]:
    findings = [label for label, pattern in PATTERNS.items() if pattern.search(text)]
    if any(
        not is_placeholder_email_domain(match.group(1)) for match in EMAIL_PATTERN.finditer(text)
    ):
        findings.append("email address")
    return findings


def tracked_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise ValueError(
            "Git is required because this guard scans tracked public files only; "
            "no recursive fallback is used"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        message = (
            "repository root must be a Git work tree because this guard scans tracked "
            "public files only; no recursive fallback is used"
        )
        raise ValueError(f"{message}: {detail}" if detail else message)
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def scan_repository(root: Path) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label in scan_text(text):
            findings.append(f"{path.relative_to(root)}: {label}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Git repository to scan",
    )
    args = parser.parse_args(argv)
    root = args.repository_root.expanduser().resolve()

    try:
        findings = scan_repository(root)
    except ValueError as error:
        print(f"Public Scan: ERROR: {error}")
        return 2

    print(f"Public Scan: {len(findings)} finding(s)")
    for finding in findings:
        print(f"ERROR: {finding}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
