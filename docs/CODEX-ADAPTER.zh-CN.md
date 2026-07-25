# Codex 省心模式适配层

> 本文把通用的主 Agent 托管模式映射到当前 Codex 配置和子 Agent 能力。

## 1. 适配目标与状态

目标是让用户只与 Sol 主 Agent 对话，由主 Agent 在后台按任务需要调用 Terra 或 Luna，并对所有结果负责。

当前模型映射以 2026-07-25 可用的 Codex 能力为准：

| 能力层级 | Codex 模型 | 主要用途 |
| --- | --- | --- |
| Frontier | `gpt-5.6-sol` | 主编排、架构、冲突裁决、高风险复核、失败重规划 |
| Balanced | `gpt-5.6-terra` | 常规开发、代码调查、测试分析、文档研究 |
| Fast | `gpt-5.6-luna` | 搜索、分类、抽取、格式转换、大批量只读扫描 |

模型名称属于适配层，可以随 Codex 能力变化；Frontier、Balanced、Fast 的职责语义属于核心协议。

## 2. Codex 配置表面

| 表面 | 负责什么 |
| --- | --- |
| `~/.codex/config.toml` | 个人默认主模型、子 Agent 兜底模型和并发上限 |
| `~/.codex/AGENTS.md` | 跨项目稳定的个人协作与路由规则 |
| 项目根 `AGENTS.md` | 当前项目的执行约定、风险和验证要求 |
| 当前任务提示 | 本轮临时目标、范围、授权和特殊模型要求 |

越靠近当前任务的明确指令优先级越高，但不能绕过系统权限和外部副作用授权。

## 3. 推荐全局配置

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
default_subagent_model = "gpt-5.6-terra"
default_subagent_reasoning_effort = "medium"
```

这组配置产生四个效果：

- 新任务默认由 Sol 主 Agent 托管。
- 子 Agent 漏写模型时兜底使用 Terra，而不是继承 Sol。
- 并行子任务最多三个，不含主 Agent。
- 默认推理强度让 Worker 保持成本与质量平衡。

兜底配置不能替代显式路由。每次委派仍应明确指定 Terra 或 Luna。

### 严格配置排障

`--strict-config` 会让当前 Codex CLI 拒绝它不认识的配置字段。如果严格校验因
`[network]` 等既有字段失败，但普通模式可以正常加载，这通常表示桌面端与 CLI
版本的配置 schema 不一致，不等于多 Agent 配置失效。

- 不要仅为了通过严格校验就删除未知字段；先确认字段由哪个 Codex 表面或版本管理。
- 验证本文配置片段时，使用隔离调用，避免真实用户配置中的其他字段干扰。
- 隔离调用仍复用 `CODEX_HOME` 中的认证信息，但不会加载其中的 `config.toml`。

```bash
codex exec --ignore-user-config --strict-config \
  -c 'model="gpt-5.6-sol"' \
  -c 'agents.enabled=true' \
  -c 'agents.default_subagent_model="gpt-5.6-terra"' \
  -c 'agents.default_subagent_reasoning_effort="medium"' \
  --ephemeral --sandbox read-only \
  'Return only CODEX_STRICT_CONFIG_OK.'
```

如果隔离调用通过，而真实配置仍被严格模式拒绝，应保留普通可用配置并记录版本差异；
不要把删除未知字段作为默认修复。判断隔离调用时以退出码和末尾的
`CODEX_STRICT_CONFIG_OK` 为准；模型列表刷新警告不等于配置 schema 校验失败。

## 4. 运行时路由

```text
先确定本轮交付物和最小垂直切片
→ 判断是否存在独立、非阻塞的子任务
→ 选择 Balanced 或 Fast
→ 用完整委派问题单创建子 Agent
→ 主 Agent 继续处理关键路径
→ 回收、复核、整合并统一交付
```

运行规则：

- Terra 是常规 Worker；Luna 只承担边界清楚、验证简单的轻量任务。
- 每次创建子 Agent 都显式传入模型，禁止依赖父任务继承。
- 默认不创建 Sol 子 Agent；复杂度或风险升级后由主 Sol 接管。
- 子 Agent 不直接向用户交付，不改变产品方向，也不独立扩大任务范围。
- 子 Agent 完成后及时关闭，避免占用并发容量。

## 5. 委派与验收契约

委派问题单必须包含目标、最小上下文、允许范围、输出格式、验收证据和升级条件。

子 Agent 返回后，主 Agent 必须：

1. 检查结果是否回答原问题单。
2. 用当前文件、测试或真实输出复核关键结论。
3. 处理不同结果之间的冲突、重复和遗漏。
4. 将结果整合回当前垂直切片。
5. 统一向用户说明证据、风险和下一步。

未经主 Agent 复核的子 Agent 输出不能作为完成证据。

## 6. 权限、失败与降级

- 子 Agent 继承当前任务的权限模式；多 Agent 不会扩大原任务权限。
- 部署、删除、真实外部写入、凭据和最终 Git 发布不得无人复核地委派。
- 子 Agent 结果冲突、信心不足、连续工具失败或风险升高时，返回主 Agent 重规划。
- 无法显式选择模型或子 Agent 不可用时，退化为主 Agent 顺序执行。
- 修改全局配置后，从新任务验证；不要假设已运行任务会被追溯切换。

## 7. 最小端到端验证

适配层只有在以下检查全部完成后才能声明“已验证”：

1. 新任务默认使用 Sol 主模型。
2. Luna 能完成一次显式指定的只读扫描并返回证据。
3. Terra 能完成一次显式指定的常规调查或测试分析。
4. 主 Sol 能审查两份结果并指出采纳或拒绝理由。
5. 权限、并发上限和失败降级符合配置。

当前仓库的本机 smoke 证据见 [Codex E2E 记录](CODEX-E2E-2026-07-25.md)。验证范围之外仍不得宣称完整兼容。

## 8. 当前非目标

- 不创建一套需要用户逐个管理的角色型 Agent 团队。
- 不为产品、前端、后端等每个名词固定绑定一个模型。
- 不引入自定义 Agent 文件，除非后续真实任务证明有必要。
- 不在核心协议中写死其他平台的模型名称和调用方式。

配置字段依据 [Codex Subagents 文档](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)。
