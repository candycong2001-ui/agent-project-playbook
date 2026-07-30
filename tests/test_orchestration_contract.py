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
        self.assertIn("Reserve capacity for verification", agents)
        self.assertIn("exclusive ownership", agents)

    def test_orchestration_contract_guards_delegation_and_recovery(self) -> None:
        protocol = read("docs/ORCHESTRATION_MODEL.zh-CN.md")

        for required in (
            "NO_DELEGATION",
            "DIRECT_MAIN",
            "FAST_SCAN",
            "BALANCED_WORK",
            "INDEPENDENT_CHECK",
            "ESCALATE_TO_MAIN",
            "P0 只读",
            "P3 真实副作用",
            "TIMEOUT → RECLAIMED",
            "角色描述“做什么”",
        ):
            with self.subTest(required=required):
                self.assertIn(required, protocol)

    def test_bilingual_templates_guard_delegation_value_and_permission(self) -> None:
        cases = (
            (
                "templates/AGENTS.md",
                "`NO_DELEGATION` is a valid route",
                "Stronger reasoning never grants wider authority",
                "`ESCALATE_TO_MAIN`",
            ),
            (
                "templates/zh-CN/AGENTS.md",
                "`NO_DELEGATION` 是正常路由结果",
                "更强推理不会自动获得更高权限",
                "`ESCALATE_TO_MAIN`",
            ),
        )
        for relative, no_delegation, permission, escalation in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(no_delegation, template)
                self.assertIn(permission, template)
                self.assertIn(escalation, template)

    def test_canonical_protocol_requires_health_probe_and_reserved_capacity(self) -> None:
        protocol = read("docs/ORCHESTRATION_MODEL.zh-CN.md")

        self.assertIn("健康探针", protocol)
        self.assertIn("reserved_slots", protocol)
        self.assertIn("不得在核心协议中写死为某个数字", protocol)

    def test_bilingual_templates_preserve_worker_ownership_and_adoption(self) -> None:
        cases = (
            (
                "templates/AGENTS.md",
                "exclusive file or module ownership",
                "Workers do not spawn agents",
                "verified and adopted its output",
            ),
            (
                "templates/zh-CN/AGENTS.md",
                "互斥的文件或模块",
                "Worker 不得继续派遣",
                "验证并采纳产物后",
            ),
        )
        for relative, ownership, no_descendants, adoption in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(ownership, template)
                self.assertIn(no_descendants, template)
                self.assertIn(adoption, template)

    def test_canonical_protocol_separates_unmaterialized_from_timeout(self) -> None:
        protocol = read("docs/ORCHESTRATION_MODEL.zh-CN.md")

        self.assertIn("SPAWNING → UNMATERIALIZED → STOP_BATCH → DIRECT", protocol)
        self.assertIn("STOP_BATCH → REPLAN", protocol)
        self.assertIn("TIMEOUT → RECLAIMED", protocol)
        self.assertIn("不得混淆", protocol)

    def test_codex_adapter_classifies_unmaterialized_and_initialization_failures(self) -> None:
        adapter = read("docs/CODEX-ADAPTER.zh-CN.md")

        for required in (
            "UNMATERIALIZED",
            "not materialized yet",
            "no rollout found",
            "INIT_BLOCKED",
            "不批量重试",
            "不得把 `project` 与 `projectless` 之间的环境类型切换当作同一故障的重试",
        ):
            with self.subTest(required=required):
                self.assertIn(required, adapter)

    def test_codex_adapter_limits_followup_and_archive_to_adopted_threads(self) -> None:
        adapter = read("docs/CODEX-ADAPTER.zh-CN.md")

        for required in (
            "只在原 thread 追问一次",
            "FORK_COST_RISK",
            "thread_id",
            "同一子目标最多两次实际执行机会",
            "禁止无条件第三次创建或重派",
            "输出已经验证且结果已采纳",
            "禁止并行连发归档请求",
            "未实体化、未验证、争议中或未采纳的 thread 不得归档",
        ):
            with self.subTest(required=required):
                self.assertIn(required, adapter)


if __name__ == "__main__":
    unittest.main()
