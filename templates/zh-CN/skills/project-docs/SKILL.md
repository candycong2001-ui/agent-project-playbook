---
name: project-docs
description: 维护当前项目中有边界的 BLUEPRINT、ARCHITECTURE 和 CURRENT_HANDOFF 文档，并运行 Docs Lint。适用于重要实施或诊断、得到授权的交接、范围或架构变化，以及文档漂移检查。
---

# 项目文档

## 流程

1. 开始重要实施或诊断时，先读 `docs/CURRENT_HANDOFF.md`。
2. 只读 `docs/BLUEPRINT.md` 和 `docs/ARCHITECTURE.md` 的相关部分。
3. 用当前仓库证据核对文档内容。
4. 探索或只读审查期间，只报告漂移；未经授权不修改文档。
5. 实施期间在 `CURRENT_HANDOFF.md` 保留一个当前协作模式、项目阶段、交付物、问题单和垂直切片。
6. 替换过时状态，不追加会话流水。
7. 只有产品意图、用户、范围、约束或验收变化时才更新 `BLUEPRINT.md`。
8. 只有组件、边界、数据流、命令、部署、回滚或风险变化时才更新 `ARCHITECTURE.md`。
9. 正式项目开始实施和发布交接前，运行 `python3 .agents/skills/project-docs/scripts/project_safety.py inspect .`。
10. 交付前运行 `python3 .agents/skills/project-docs/scripts/docs_lint.py`。

## 真值与大小限制

- 当前代码、测试、配置、命令输出和用户指令高于这些文档。
- BLUEPRINT 不超过 160 行。
- ARCHITECTURE 不超过 220 行。
- CURRENT_HANDOFF 不超过 120 行。
- AGENTS 不超过 180 行。
