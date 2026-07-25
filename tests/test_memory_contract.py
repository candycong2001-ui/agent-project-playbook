from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY_MODEL = ROOT / "docs" / "MEMORY_MODEL.zh-CN.md"


class MemoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = MEMORY_MODEL.read_text(encoding="utf-8")

    def test_declares_three_memory_scopes(self) -> None:
        for scope in ("当前任务", "当前项目", "全局协作"):
            with self.subTest(scope=scope):
                self.assertIn(f"| {scope} |", self.model)

    def test_declares_four_trust_states(self) -> None:
        for state in ("候选", "已验证", "待复核", "已废弃"):
            with self.subTest(state=state):
                self.assertIn(f"| {state} |", self.model)

    def test_preserves_truth_order(self) -> None:
        expected_order = (
            "用户本轮明确指令",
            "当前代码、测试、配置和真实输出",
            "已确认的稳定项目文档",
            "已验证的项目记忆",
            "候选或待复核记忆",
            "聊天历史",
        )
        positions = [self.model.index(item) for item in expected_order]

        self.assertEqual(positions, sorted(positions))

    def test_preserves_five_promotion_rules(self) -> None:
        section = self.model.split("## 5. 记忆晋升流程", maxsplit=1)[1]
        section = section.split("## 6. 检索与冲突处理", maxsplit=1)[0]
        rules = re.findall(r"(?m)^\d+\. .+$", section)

        self.assertEqual(len(rules), 5)
        for anchor in (
            "默认不把每轮对话写入长期记忆",
            "才进入候选",
            "不得升级为已验证",
            "才能进入全局",
            "应更新状态",
        ):
            with self.subTest(anchor=anchor):
                self.assertTrue(any(anchor in rule for rule in rules))

    def test_declares_runtime_enforcement_boundary(self) -> None:
        self.assertIn("不提供运行时强制隔离、自动状态迁移或可信度判定", self.model)
        self.assertIn("安装本章程不等于安装独立的记忆引擎", self.model)


if __name__ == "__main__":
    unittest.main()
