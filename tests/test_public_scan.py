from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.scan_public_repo import scan_repository, scan_text


class PublicScanTests(unittest.TestCase):
    def test_reserved_example_email_domains_are_allowed(self) -> None:
        for domain in (
            "example.com",
            "docs.example.com",
            "example.org",
            "example.net",
            "team.example",
            "docs.test",
            "site.invalid",
        ):
            self.assertEqual(scan_text(f"user@{domain}"), [])

    def test_non_placeholder_email_is_detected(self) -> None:
        address = "person@" + "real-company.com"
        self.assertIn("email address", scan_text(address))

    def test_only_tracked_files_are_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            tracked = root / "tracked.md"
            tracked.write_text("contact: user@example.com\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.md"], check=True)

            untracked = root / "local.txt"
            untracked.write_text("contact: person@" + "real-company.com\n", encoding="utf-8")

            self.assertEqual(scan_repository(root), [])


if __name__ == "__main__":
    unittest.main()
