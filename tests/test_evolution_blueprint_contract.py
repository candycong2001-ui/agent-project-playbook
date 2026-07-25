from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "docs" / "EVOLUTION_BLUEPRINT.zh-CN.md"


class EvolutionBlueprintContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.blueprint = BLUEPRINT.read_text(encoding="utf-8")

    def test_declares_core_architecture(self) -> None:
        for anchor in (
            "一条项目主线",
            "两台协作引擎",
            "三道长期护栏",
            "四期演进路线",
            "理解 → 编排 → 执行 → 验证 → 记忆 → 更好的理解",
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.blueprint)

    def test_declares_three_memory_layers_and_promotion_gate(self) -> None:
        for layer in ("任务记忆", "项目记忆", "全局记忆"):
            with self.subTest(layer=layer):
                self.assertIn(f"| {layer} |", self.blueprint)

        for gate in ("多项目重复验证", "全局候选", "人工确认"):
            with self.subTest(gate=gate):
                self.assertIn(gate, self.blueprint)

    def test_declares_two_engine_exchange_contract(self) -> None:
        self.assertIn("| 记忆 → 编排 |", self.blueprint)
        self.assertIn("| 编排 → 记忆 |", self.blueprint)
        self.assertIn("记忆引擎让主 Agent 更好地理解意图", self.blueprint)

    def test_separates_current_delivery_from_future_roadmap(self) -> None:
        expected = {
            "Phase I：结构化": "当前已实现",
            "Phase II：可检索、可路由": "下一阶段",
            "Phase III：可关联、可续跑": "规划阶段",
            "Phase IV：可学习、受治理": "远期方向",
        }
        for phase, status in expected.items():
            with self.subTest(phase=phase):
                self.assertIn(phase, self.blueprint)
                self.assertIn(status, self.blueprint)

        self.assertIn("不是对尚未实现能力的声明", self.blueprint)

    def test_preserves_governance_and_portability(self) -> None:
        for anchor in (
            "当前证据高于历史记忆",
            "项目隔离与显式晋升",
            "人类最终授权",
            "模型可以替换",
            "Human-Governed Evolution",
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.blueprint)

    def test_readme_links_the_blueprint(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "docs/EVOLUTION_BLUEPRINT.zh-CN.md",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
