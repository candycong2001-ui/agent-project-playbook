from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "init_projectmem.py"


def make_fake_pjm(directory: Path) -> Path:
    binary = directory / "pjm"
    binary.write_text(
        """#!/usr/bin/env python3
import os
import sys
from pathlib import Path

Path(os.environ["FAKE_PJM_ARGS"]).write_text("\\n".join(sys.argv[1:]), encoding="utf-8")
if len(sys.argv) > 1 and sys.argv[1] == "init":
    root = Path.cwd() / ".projectmem"
    root.mkdir()
    (root / "AI_INSTRUCTIONS.md").write_text("generated instructions\\n", encoding="utf-8")
    (root / "PROJECT_MAP.md").write_text("# Project Map\\n", encoding="utf-8")
    (root / "config.toml").write_text(
        'summary_size_limit_kb = 20\\nrecent_days = 30\\nproject_description = ""\\n',
        encoding="utf-8",
    )
    (root / "events.jsonl").write_text("", encoding="utf-8")
    (root / "summary.md").write_text("# Project Memory\\n", encoding="utf-8")
    print("Initialized quiet projectmem")
    raise SystemExit(0)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return binary


def run_adapter(project: Path, fake_pjm: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PJM_BIN"] = str(fake_pjm)
    environment["FAKE_PJM_ARGS"] = str(project / "pjm-args.txt")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            str(project),
            "--project-name",
            "demo",
            "--locale",
            "zh-CN",
            *extra,
        ],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class ProjectmemAdapterTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_adapter(project, fake)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("quiet pjm init", result.stdout)
            self.assertFalse(any(project.iterdir()))

    def test_apply_installs_quiet_projectmem_and_cold_memory_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)

            result = run_adapter(project, fake, "--apply")

            self.assertEqual(result.returncode, 0, result.stdout)
            args = (project / "pjm-args.txt").read_text(encoding="utf-8")
            for flag in (
                "--no-hooks",
                "--no-global",
                "--no-watch",
                "--no-backfill",
                "--no-claude-md",
                "--no-stack-detect",
                "--no-mcp-config",
            ):
                self.assertIn(flag, args)

            config = (project / ".projectmem/config.toml").read_text(encoding="utf-8")
            self.assertIn("auto_capture = false", config)
            instructions = (project / ".projectmem/AI_INSTRUCTIONS.md").read_text(encoding="utf-8")
            self.assertIn("Projectmem 是当前仓库的冷记忆", instructions)
            skill = (project / ".agents/skills/project-memory/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: project-memory", skill)
            self.assertIn("当前仓库证据才是真值源", skill)
            ignores = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".projectmem/events.jsonl", ignores)
            self.assertIn(".projectmem/watch.log", ignores)

    def test_existing_projectmem_blocks_without_other_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            (project / ".projectmem").mkdir(parents=True)
            fake = make_fake_pjm(root)

            result = run_adapter(project, fake, "--apply")

            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn(".projectmem exists", result.stdout)
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / ".gitignore").exists())

    def test_upgrade_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            fake = make_fake_pjm(root)
            installed = run_adapter(project, fake, "--apply")
            self.assertEqual(installed.returncode, 0, installed.stdout)
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = run_adapter(project, fake, "--upgrade")

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- mode: `read-only`", result.stdout)
            after = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
