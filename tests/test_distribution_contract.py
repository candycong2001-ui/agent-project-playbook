from __future__ import annotations

import unittest
from pathlib import Path

from scripts.init_project import DESTINATIONS, template_files

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
        for locale in ("en", "zh-CN"):
            with self.subTest(locale=locale):
                files = template_files(locale)
                self.assertEqual(tuple(files), DESTINATIONS)
                for source in files.values():
                    self.assertTrue(source.is_file(), source)

    def test_source_skills_have_required_frontmatter(self) -> None:
        skills = (
            ROOT / "skills" / "agent-project-bootstrap" / "SKILL.md",
            ROOT / "templates" / "skills" / "project-docs" / "SKILL.md",
            ROOT / "templates" / "zh-CN" / "skills" / "project-docs" / "SKILL.md",
        )
        for path in skills:
            with self.subTest(path=path):
                metadata = frontmatter(path)
                self.assertTrue(metadata.get("name"))
                self.assertTrue(metadata.get("description"))
                self.assertEqual(set(metadata), {"name", "description"})


if __name__ == "__main__":
    unittest.main()
