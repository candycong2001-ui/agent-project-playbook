from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "scripts" / "init_project.py"

EXPECTED_FILES = (
    "AGENTS.md",
    "docs/BLUEPRINT.md",
    "docs/ARCHITECTURE.md",
    "docs/CURRENT_HANDOFF.md",
    ".agents/skills/project-docs/SKILL.md",
    ".agents/skills/project-docs/scripts/docs_lint.py",
)


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def initialize(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            str(INITIALIZER),
            str(project),
            "--project-name",
            "demo-project",
            *extra,
        ]
    )


class InitProjectTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- mode: `dry-run`", result.stdout)
            self.assertFalse(any(project.iterdir()))

    def test_apply_creates_complete_playbook_and_lint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            for relative in EXPECTED_FILES:
                self.assertTrue((project / relative).exists(), relative)

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# demo-project Working Agreement", agents)
            self.assertIn("## Design Thinking mapping", agents)
            self.assertIn("## Automatic two-level task routing", agents)

            handoff = (project / "docs/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("Collaboration mode:", handoff)
            self.assertIn("Project stage:", handoff)
            self.assertIn("Current deliverable:", handoff)
            self.assertIn("Role assignment", handoff)

            lint = run(
                [sys.executable, ".agents/skills/project-docs/scripts/docs_lint.py"],
                cwd=project,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("Docs Lint: 0 error(s)", lint.stdout)

    def test_existing_file_blocks_the_entire_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("existing rules\n", encoding="utf-8")

            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertEqual(agents.read_text(encoding="utf-8"), "existing rules\n")
            self.assertIn("AGENTS.md exists; merge manually", result.stdout)
            self.assertFalse((project / "docs").exists())
            self.assertFalse((project / ".agents").exists())

    def test_symbolic_link_escape_is_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            outside = root / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "docs").symlink_to(outside, target_is_directory=True)

            result = initialize(project, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("symbolic link is not allowed", result.stdout)
            self.assertFalse(any(outside.iterdir()))
            self.assertFalse((project / "AGENTS.md").exists())

    def test_public_files_do_not_contain_sensitive_artifacts(self) -> None:
        sensitive_patterns = {
            "user home path": re.compile(r"/(?:Users|home)/[^/\s\"']+/"),
            "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
            "GitHub token": re.compile(
                rf"\b(?:gh[pousr]_[A-Za-z0-9_]{{20,}}|{'github' + '_pat_'}[A-Za-z0-9_]{{20,}})"
            ),
            "API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
            "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        }
        public_files = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        ]

        for path in public_files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in sensitive_patterns.items():
                self.assertIsNone(pattern.search(text), f"{label} found in {path}")


if __name__ == "__main__":
    unittest.main()
