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

    def test_bilingual_routing_skills_keep_model_and_permission_separate(self) -> None:
        cases = (
            (
                "templates/skills/multi-agent-routing/SKILL.md",
                "Match capability and reasoning depth to the task",
                "stronger reasoning does not grant broader permissions",
            ),
            (
                "templates/zh-CN/skills/multi-agent-routing/SKILL.md",
                "能力与推理深度按任务选择",
                "更强推理不会获得更宽权限",
            ),
        )
        for relative, capability_route, permission_boundary in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(capability_route, template)
                self.assertIn(permission_boundary, template)

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

    def test_bilingual_routing_skills_guard_delegation_value(self) -> None:
        cases = (
            (
                "templates/skills/multi-agent-routing/SKILL.md",
                "`NO_DELEGATION` is a normal result",
                "Workers do not create more workers",
                "The lead verifies material claims",
            ),
            (
                "templates/zh-CN/skills/multi-agent-routing/SKILL.md",
                "`NO_DELEGATION` 是正常结果",
                "Worker 不继续创建 Worker",
                "主 Agent 用当前文件",
            ),
        )
        for relative, no_delegation, no_descendants, verification in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(no_delegation, template)
                self.assertIn(no_descendants, template)
                self.assertIn(verification, template)

    def test_canonical_protocol_requires_health_probe_and_reserved_capacity(self) -> None:
        protocol = read("docs/ORCHESTRATION_MODEL.zh-CN.md")

        self.assertIn("健康探针", protocol)
        self.assertIn("reserved_slots", protocol)
        self.assertIn("不得在核心协议中写死为某个数字", protocol)

    def test_bilingual_routing_skills_preserve_worker_ownership(self) -> None:
        cases = (
            (
                "templates/skills/multi-agent-routing/SKILL.md",
                "owned files or surface",
                "expected artifact",
                "evidence required",
            ),
            (
                "templates/zh-CN/skills/multi-agent-routing/SKILL.md",
                "负责文件或范围",
                "预期产物",
                "所需证据",
            ),
        )
        for relative, ownership, artifact, evidence in cases:
            with self.subTest(relative=relative):
                template = read(relative)
                self.assertIn(ownership, template)
                self.assertIn(artifact, template)
                self.assertIn(evidence, template)

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
