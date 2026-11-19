---
name: project-docs
description: 维护有边界的 BLUEPRINT、ARCHITECTURE 和 CURRENT_HANDOFF 文档，并运行 Docs Lint。适用于重要实施或诊断、得到授权的交接、范围或架构变化，以及文档漂移检查；普通小修不触发。
---

# 项目文档

## 流程

1. 开始重要实施或诊断时，先读 `docs/CURRENT_HANDOFF.md`，再按需读稳定文档的相关部分。
2. 用当前仓库证据核对文档内容。
3. 探索或只读审查期间，未经用户授权只报告漂移，不修改文档。
4. 第 4—8 步涉及的文档修改需要授权。实施任务开始时，在 `CURRENT_HANDOFF.md` 更新所涉事项的目标和下一步，保留其他未完工作。
5. 得到可验证成果后，在原处更新所涉事项的状态和证据，保留其他未完工作接续所需的链接。
6. 移出已完成过程前先确认必要依据可恢复，包括只在本地或未进入 Git 历史的资料。
7. 只有产品意图、用户、范围、约束或验收变化时才更新 `BLUEPRINT.md`。
8. 只有组件、边界、数据流、已验证命令、部署、回滚或风险变化时才更新 `ARCHITECTURE.md`。
9. 重要交付前，或只读审阅需要核对文档结构时，运行 `python3 .agents/skills/project-docs/scripts/docs_lint.py`。运行 Lint 不授予修改文档的权限。

## 边界

- 用户决定说明意图和授权；当前代码、测试、配置和命令输出说明实际结果。
- BLUEPRINT 和 ARCHITECTURE 各 160 行、CURRENT_HANDOFF 80 行、AGENTS 90 行，超出时告警以提示整理。保留接续所需的信息和必需结构。
