---
name: project-docs
description: 维护有边界的 BLUEPRINT、ARCHITECTURE 和 CURRENT_HANDOFF 文档，并运行 Docs Lint。适用于重要实施或诊断、得到授权的交接、范围或架构变化，以及文档漂移检查；普通小修不触发。
---

# 项目文档

## 流程

1. 开始重要实施或诊断时，先读 `docs/CURRENT_HANDOFF.md`，再按需读稳定文档的相关部分。
2. 用当前仓库证据核对文档内容。
3. 探索或只读审查期间，未经用户授权只报告漂移，不修改文档。
4. 任务开始时，替换 `CURRENT_HANDOFF.md` 的当前目标和下一步。
5. 得到可验证成果后，替换当前状态和验证证据，不追加时间线。
6. 交接前删除已经完成的过程，只留下可以继续工作的单一当前状态。
7. 只有产品意图、用户、范围、约束或验收变化时才更新 `BLUEPRINT.md`。
8. 只有组件、边界、数据流、已验证命令、部署、回滚或风险变化时才更新 `ARCHITECTURE.md`。
9. 重要交付前运行 `python3 .agents/skills/project-docs/scripts/docs_lint.py`。

## 边界

- 当前代码、测试、配置、命令输出和用户指令高于这些文档。
- BLUEPRINT 不超过 160 行。
- ARCHITECTURE 不超过 160 行。
- CURRENT_HANDOFF 不超过 80 行。
- AGENTS 不超过 90 行。
- Git 保存历史；CURRENT_HANDOFF 只保存最新工作状态。
