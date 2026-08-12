from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = json.loads((ROOT / "playbook_contract.json").read_text(encoding="utf-8"))[
    "playbook_version"
]


def copy_repository(destination: Path) -> Path:
    target = destination / "repository"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    return target


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "check_invariants.py"), "--repo-root", str(root)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class PlaybookInvariantTests(unittest.TestCase):
    def test_current_repository_satisfies_invariants(self) -> None:
        result = run_checker(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Invariant Check: 0 error(s)", result.stdout)

    def test_each_document_version_drift_fails(self) -> None:
        mutations = {
            "README.md": (
                f"当前版本：`v{CURRENT_VERSION}`",
                "当前版本：`v0.0.0`",
            ),
            "docs/PORTABILITY.zh-CN.md": (
                f"## v{CURRENT_VERSION} 兼容性矩阵",
                "## v0.0.0 兼容性矩阵",
            ),
            "docs/EVOLUTION_BLUEPRINT.zh-CN.md": (
                f"当前 `v{CURRENT_VERSION}` ",
                "当前 `v0.0.0` ",
            ),
        }
        for relative, (old, new) in mutations.items():
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                root = copy_repository(Path(temporary))
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
                )

                result = run_checker(root)

                self.assertEqual(result.returncode, 1, result.stdout)

    def test_projectmem_default_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_repository(Path(temporary))
            path = root / "playbook_contract.json"
            contract = json.loads(path.read_text(encoding="utf-8"))
            contract["defaults"]["projectmem"] = "automatic"
            contract["capabilities"]["projectmem"]["activation"] = "automatic"
            path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            result = run_checker(root)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("projectmem", result.stdout)

    def test_capability_cannot_leak_into_another_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_repository(Path(temporary))
            path = root / "playbook_contract.json"
            contract = json.loads(path.read_text(encoding="utf-8"))
            destination = ".agents/skills/production-release-gate/SKILL.md"
            contract["profiles"]["simple"]["destinations"].append(destination)
            path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            result = run_checker(root)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("production-release-gate", result.stdout)

    def test_roadmap_status_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_repository(Path(temporary))
            path = root / "docs" / "EVOLUTION_BLUEPRINT.zh-CN.md"
            text = path.read_text(encoding="utf-8").replace("当前已实现", "状态未知", 1)
            path.write_text(text, encoding="utf-8")

            result = run_checker(root)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("Phase I", result.stdout)

    def test_profile_destination_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_repository(Path(temporary))
            path = root / "playbook_contract.json"
            contract = json.loads(path.read_text(encoding="utf-8"))
            contract["profiles"]["simple"]["destinations"].append("missing/SKILL.md")
            path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            result = run_checker(root)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("template destinations differ", result.stdout)

    def test_malformed_contract_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_repository(Path(temporary))
            (root / "playbook_contract.json").write_text("{not-json}\n", encoding="utf-8")

            result = run_checker(root)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("invalid playbook_contract.json", result.stdout)
            self.assertNotIn("Traceback", result.stdout)


if __name__ == "__main__":
    unittest.main()
