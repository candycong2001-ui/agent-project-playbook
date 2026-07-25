from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class OrchestrationContractTests(unittest.TestCase):
    def test_codex_adapter_declares_three_tier_mapping(self) -> None:
        adapter = read("docs/CODEX-ADAPTER.zh-CN.md")

        expected = {
            "Frontier": "gpt-5.6-sol",
            "Balanced": "gpt-5.6-terra",
            "Fast": "gpt-5.6-luna",
        }
        for tier, model in expected.items():
            with self.subTest(tier=tier):
                self.assertIn(tier, adapter)
                self.assertIn(f"`{model}`", adapter)

    def test_recommended_config_uses_sol_main_and_terra_fallback(self) -> None:
        adapter = read("docs/CODEX-ADAPTER.zh-CN.md")
        match = re.search(r"```toml\n(?P<config>.*?)```", adapter, re.DOTALL)

        self.assertIsNotNone(match)
        config = match.group("config")
        self.assertIn('model = "gpt-5.6-sol"', config)
        self.assertIn('default_subagent_model = "gpt-5.6-terra"', config)
        self.assertIn("max_concurrent_threads_per_session = 3", config)

    def test_bilingual_templates_require_explicit_worker_models(self) -> None:
        cases = (
            (
                "templates/AGENTS.md",
                "Every subagent spawn must explicitly select Terra or Luna.",
                "Do not create Sol subagents by default",
            ),
            (
                "templates/zh-CN/AGENTS.md",
                "创建子 Agent 时必须显式选择 Terra 或 Luna",
                "默认不创建 Sol 子 Agent",
            ),
        )
        for relative, explicit_route, no_sol_worker in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(explicit_route, template)
                self.assertIn(no_sol_worker, template)

    def test_repository_dogfoods_manager_mode(self) -> None:
        agents = read("AGENTS.md")

        self.assertIn("## Manager mode", agents)
        self.assertIn("Sol / Frontier", agents)
        self.assertIn("Terra / Balanced", agents)
        self.assertIn("Luna / Fast", agents)
        self.assertIn("Do not create Sol subagents by default", agents)


if __name__ == "__main__":
    unittest.main()
