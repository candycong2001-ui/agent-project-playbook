from __future__ import annotations

import unittest
from pathlib import Path

from scripts.init_project import DESTINATIONS, profile_destinations, template_files

ROOT = Path(__file__).resolve().parents[1]


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise AssertionError(f"missing YAML frontmatter: {path}")
    end = lines[1:].index("---") + 1
    values: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values


class DistributionContractTests(unittest.TestCase):
    def test_every_locale_has_the_complete_template_set(self) -> None:
        self.assertEqual(DESTINATIONS, profile_destinations("simple"))
        for locale in ("en", "zh-CN"):
            for profile in ("simple", "production"):
                with self.subTest(locale=locale, profile=profile):
                    files = template_files(locale, profile)
                    self.assertEqual(tuple(files), profile_destinations(profile))
                    for source in files.values():
                        self.assertTrue(source.is_file(), source)

    def test_source_skills_have_required_frontmatter(self) -> None:
        skills = (
            ROOT / "skills" / "agent-project-bootstrap" / "SKILL.md",
            ROOT / "templates" / "skills" / "project-lifecycle" / "SKILL.md",
            ROOT / "templates" / "zh-CN" / "skills" / "project-lifecycle" / "SKILL.md",
            ROOT / "templates" / "skills" / "multi-agent-routing" / "SKILL.md",
            ROOT / "templates" / "zh-CN" / "skills" / "multi-agent-routing" / "SKILL.md",
            ROOT / "templates" / "skills" / "project-docs" / "SKILL.md",
            ROOT / "templates" / "zh-CN" / "skills" / "project-docs" / "SKILL.md",
            ROOT / "templates" / "skills" / "production-release-gate" / "SKILL.md",
            ROOT / "templates" / "zh-CN" / "skills" / "production-release-gate" / "SKILL.md",
            ROOT
            / "adapters"
            / "projectmem"
            / "templates"
            / "en"
            / "skills"
            / "project-memory"
            / "SKILL.md",
            ROOT
            / "adapters"
            / "projectmem"
            / "templates"
            / "zh-CN"
            / "skills"
            / "project-memory"
            / "SKILL.md",
            ROOT / "adapters" / "codex" / "new-project-memory-bootstrap" / "SKILL.md",
        )
        for path in skills:
            with self.subTest(path=path):
                metadata = frontmatter(path)
                self.assertTrue(metadata.get("name"))
                self.assertTrue(metadata.get("description"))
                self.assertEqual(set(metadata), {"name", "description"})

    def test_lifecycle_skills_preserve_design_thinking_without_bloating_agents(self) -> None:
        cases = (
            (
                ROOT / "templates" / "skills" / "project-lifecycle" / "SKILL.md",
                "## Design Thinking bridge",
                "Keep a small low-risk task to one sentence",
            ),
            (
                ROOT / "templates" / "zh-CN" / "skills" / "project-lifecycle" / "SKILL.md",
                "## Design Thinking 衔接",
                "普通低风险小任务用一句话",
            ),
        )
        for skill, thinking, proportionality in cases:
            with self.subTest(skill=skill):
                text = skill.read_text(encoding="utf-8")
                self.assertIn(thinking, text)
                self.assertIn(proportionality, text)

    def test_production_skills_route_changes_by_affected_surface(self) -> None:
        cases = (
            (
                ROOT / "templates" / "skills" / "production-release-gate" / "SKILL.md",
                ("Documentation only", "Frontend/static assets", "Backend/API", "Dependency"),
                "Do not invent a backup, restart, or environment layer",
            ),
            (
                ROOT / "templates" / "zh-CN" / "skills" / "production-release-gate" / "SKILL.md",
                ("仅文档", "前端或静态资源", "后端或 API", "依赖"),
                "不要凭空增加",
            ),
        )
        for skill, surfaces, proportionality in cases:
            with self.subTest(skill=skill):
                text = skill.read_text(encoding="utf-8")
                for surface in surfaces:
                    self.assertIn(surface, text)
                self.assertIn(proportionality, text)


if __name__ == "__main__":
    unittest.main()
