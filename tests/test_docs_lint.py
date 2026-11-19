from __future__ import annotations

import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "scripts" / "init_project.py"
SOURCE_LINTER = ROOT / "templates" / "skills" / "project-docs" / "scripts" / "docs_lint.py"
LINTER_NAMESPACE = runpy.run_path(str(SOURCE_LINTER))
HEADING_CONTRACT = LINTER_NAMESPACE["HEADING_CONTRACT"]
RULES = LINTER_NAMESPACE["RULES"]
EXTRACT_H2 = LINTER_NAMESPACE["extract_h2"]
LINT_PROJECT = LINTER_NAMESPACE["lint_project"]


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


def install_project(project: Path, locale: str = "en") -> None:
    result = run(
        [
            sys.executable,
            str(INITIALIZER),
            str(project),
            "--project-name",
            "lint-demo",
            "--locale",
            locale,
            "--apply",
        ]
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout)


def run_installed_lint(project: Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    linter = project / ".agents" / "skills" / "project-docs" / "scripts" / "docs_lint.py"
    return run([sys.executable, str(linter)], cwd=cwd)


class DocsLintTests(unittest.TestCase):
    def test_source_templates_pass_direct_lint(self) -> None:
        cases = (
            ("en", ROOT / "templates"),
            ("zh-CN", ROOT / "templates" / "zh-CN"),
        )
        for language, project_root in cases:
            with self.subTest(language=language):
                result = run(
                    [
                        sys.executable,
                        str(SOURCE_LINTER),
                        "--project-root",
                        str(project_root),
                        "--language",
                        language,
                    ]
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("Docs Lint: 0 error(s)", result.stdout)

    def test_rule_contract_matches_every_template_heading(self) -> None:
        cases = (
            ("en", ROOT / "templates"),
            ("zh-CN", ROOT / "templates" / "zh-CN"),
        )
        for language, template_root in cases:
            for relative, (_, required_headings) in RULES[language].items():
                with self.subTest(language=language, relative=relative):
                    text = (template_root / relative).read_text(encoding="utf-8")
                    self.assertEqual(EXTRACT_H2(text), required_headings)

    def test_bilingual_rules_share_one_semantic_heading_contract(self) -> None:
        self.assertEqual(RULES["en"].keys(), RULES["zh-CN"].keys())
        for relative, (line_limit, sections) in HEADING_CONTRACT.items():
            with self.subTest(relative=relative):
                en_limit, en_headings = RULES["en"][relative]
                zh_limit, zh_headings = RULES["zh-CN"][relative]
                semantic_keys = tuple(section[0] for section in sections)

                self.assertEqual(en_limit, line_limit)
                self.assertEqual(zh_limit, line_limit)
                self.assertEqual(len(semantic_keys), len(set(semantic_keys)))
                self.assertEqual(len(en_headings), len(zh_headings))
                self.assertEqual(en_headings, tuple(section[1] for section in sections))
                self.assertEqual(zh_headings, tuple(section[2] for section in sections))

    def test_document_warning_thresholds_are_fixed(self) -> None:
        self.assertEqual(RULES["en"]["AGENTS.md"][0], 90)
        self.assertEqual(RULES["en"]["docs/BLUEPRINT.md"][0], 160)
        self.assertEqual(RULES["en"]["docs/ARCHITECTURE.md"][0], 160)
        self.assertEqual(RULES["en"]["docs/CURRENT_HANDOFF.md"][0], 80)

    def test_installed_linter_finds_project_from_non_project_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            outside = root / "outside"
            project.mkdir()
            outside.mkdir()
            install_project(project)

            result = run_installed_lint(project, cwd=outside)

            self.assertEqual(result.returncode, 0, result.stdout)

    def test_auto_detection_skips_intermediate_docs_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            nested = project / "workspace"
            orphan_docs = nested / "docs"
            copied_linter = nested / "tools" / "docs_lint.py"
            project.mkdir()
            orphan_docs.mkdir(parents=True)
            copied_linter.parent.mkdir()
            install_project(project)
            shutil.copy2(SOURCE_LINTER, copied_linter)

            result = run([sys.executable, str(copied_linter)], cwd=nested)

            self.assertEqual(result.returncode, 0, result.stdout)

    def test_explicit_incomplete_root_reports_missing_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run(
                [
                    sys.executable,
                    str(SOURCE_LINTER),
                    "--project-root",
                    temporary,
                ]
            )

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("missing: AGENTS.md", result.stdout)
            self.assertIn("missing: docs/BLUEPRINT.md", result.stdout)

    def test_auto_detection_failure_has_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            orphan_linter = root / "tools" / "docs_lint.py"
            orphan_linter.parent.mkdir()
            shutil.copy2(SOURCE_LINTER, orphan_linter)

            result = run([sys.executable, str(orphan_linter)], cwd=root)

            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("could not locate the project root", result.stdout)

    def test_overlong_document_warns_without_hiding_structural_errors(self) -> None:
        for locale in ("en", "zh-CN"):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                install_project(project, locale=locale)
                blueprint = project / "docs" / "BLUEPRINT.md"
                overlong = blueprint.read_text(encoding="utf-8") + "\n" + ("extra\n" * 170)
                blueprint.write_text(overlong, encoding="utf-8")

                result = run_installed_lint(project)

                warning = "WARN: too long: docs/BLUEPRINT.md"
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(warning, result.stdout)

                heading = RULES[locale]["docs/BLUEPRINT.md"][1][0]
                blueprint.write_text(overlong.replace(heading, "", 1), encoding="utf-8")
                result = run_installed_lint(project)

                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(warning, result.stdout)
                self.assertIn(f"missing heading: docs/BLUEPRINT.md: {heading}", result.stdout)

    def test_lint_project_returns_structured_errors_directly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            blueprint = project / "docs" / "BLUEPRINT.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8").replace("## Purpose", "")
                + "\n## Acceptance\n",
                encoding="utf-8",
            )

            errors, warnings = LINT_PROJECT(project, "en")

            self.assertIn("missing heading: docs/BLUEPRINT.md: ## Purpose", errors)
            self.assertIn("duplicate heading: docs/BLUEPRINT.md: ## Acceptance", errors)
            self.assertEqual(
                warnings,
                [
                    "ARCHITECTURE still contains unverified placeholders",
                    "CURRENT_HANDOFF has not been activated yet",
                ],
            )

    def test_similar_heading_does_not_satisfy_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            blueprint = project / "docs" / "BLUEPRINT.md"
            text = blueprint.read_text(encoding="utf-8")
            blueprint.write_text(
                text.replace("## Purpose", "## Purpose and audience"),
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("missing heading: docs/BLUEPRINT.md: ## Purpose", result.stdout)

    def test_duplicate_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            blueprint = project / "docs" / "BLUEPRINT.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\n## Purpose\n",
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("duplicate heading: docs/BLUEPRINT.md: ## Purpose", result.stdout)

    def test_session_log_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            handoff = project / "docs" / "CURRENT_HANDOFF.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8") + "\n## Session log\n",
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("must remain current state, not an activity diary", result.stdout)

    def test_deployment_log_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            handoff = project / "docs" / "CURRENT_HANDOFF.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8") + "\n## Deployment log\n",
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("must remain current state, not an activity diary", result.stdout)

    def test_duplicate_last_updated_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            handoff = project / "docs" / "CURRENT_HANDOFF.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8") + "\nLast updated: later\n",
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("exactly one current Last updated marker", result.stdout)

    def test_dated_activity_stream_warns_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            install_project(project)
            handoff = project / "docs" / "CURRENT_HANDOFF.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8")
                + "\n- 2026-08-01 deployed\n- 2026-08-02 checked\n- 2026-08-03 restarted\n",
                encoding="utf-8",
            )

            result = run_installed_lint(project)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("looks like a dated activity stream", result.stdout)


if __name__ == "__main__":
    unittest.main()
