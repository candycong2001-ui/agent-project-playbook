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

    def test_distinguishes_authorization_from_observed_state(self) -> None:
        self.assertIn("用户本轮明确决定说明当前意图、范围和授权", self.model)
        self.assertIn("当前代码、测试、配置和真实输出说明实现、验证和运行状态", self.model)
        self.assertIn("已批准、已实现、已部署和已验收应分别记录", self.model)

    def test_keeps_native_memory_settings_separate_from_durable_writes(self) -> None:
        self.assertIn("原生记忆沿用用户已确认的宿主设置", self.model)
        self.assertIn("主动写入长期项目记忆或跨项目晋升按其授权办理", self.model)

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
