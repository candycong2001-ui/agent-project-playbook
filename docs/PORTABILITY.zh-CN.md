# 可移植性与平台适配

## 核心与适配层

这套章程不是某一个模型的专属提示词。仓库把内容分成两层：

1. 核心层：项目主线、三种模式、Design Thinking、任务路由、垂直切片、记忆模型、主 Agent 托管和风险验证。
2. 适配层：不同 Agent 平台如何加载规则、选择模型、调用子 Agent、配置权限、Skill、命令和记忆工具。

平台适配层可以变化，核心协作语义应保持一致。

## 当前版本直接提供

- 中英文 `AGENTS.md` 项目规则模板。
- Agent Skills 格式的项目启动 Skill。
- 蓝图、架构和当前交接模板。
- 不覆盖已有文件、默认 dry-run 的 Python 初始化器。
- 统一 `meminit` 入口与可选的安静模式 projectmem 适配器。
- 文档结构检查和自动化测试。
- Codex 省心模式的配置与路由设计。

## v0.3.0 兼容性矩阵

| 能力或平台 | 自动契约测试 | 真实平台 E2E | 当前状态 |
| --- | --- | --- | --- |
| 初始化器与中英文模板 | 有 | 不适用 | 可用 |
| `meminit` 与 projectmem 适配器 | 有 | 本机 CLI | 候选验证 |
| 通用 `AGENTS.md` 布局 | 有 | 未进行 | 布局约定 |
| Agent Skills frontmatter 与安装路径 | 有 | 未进行 | 结构验证 |
| Codex 省心模式 | 有 | 本机 smoke | 有限验证 |
| Claude Code | 无适配器 | 未进行 | 未支持 |
| WorkBuddy | 无适配器 | 未进行 | 未支持 |
| 通用 Prompt | 文档可人工复制 | 未进行 | 参考用 |

“自动契约测试”只证明文件生成、标题契约、安全边界和 Docs Lint 可以运行，不能替代 Agent 在真实平台中发现、加载并遵循规则的端到端证据。

## 不同平台的使用方式

### Codex

Codex 适配采用 Sol 主 Agent、Terra 常规 Worker 和 Luna 轻量 Worker。个人默认模型与子 Agent 兜底写入 `~/.codex/config.toml`，跨项目规则写入全局 `AGENTS.md`，项目规则安装到项目根 `AGENTS.md`。具体配置、路由和降级规则见 [Codex 省心模式适配层](CODEX-ADAPTER.zh-CN.md)，本机验证范围见 [Codex E2E 记录](CODEX-E2E-2026-07-25.md)。

### 支持 Agent Skills 的工具

可以复用 `skills/agent-project-bootstrap/SKILL.md` 的核心流程。工具名称、授权机制和文件发现规则应在平台适配层覆盖，不应写死进核心协议。

### Claude Code 或类似工具

把 `templates/AGENTS.md` 的语义翻译到该平台认可的项目规则文件，例如 `CLAUDE.md`。不要简单复制平台不认识的命令或工具名称。

### WorkBuddy 等具有自定义 Skill 格式的平台

保留核心流程，增加该平台需要的 manifest、入口和展示元数据。只有在目标平台真实安装并完成一次端到端测试后，才能宣称“支持”。

### 不支持规则文件的 Agent

可把 `docs/PROTOCOL.zh-CN.md` 作为系统提示词或项目协作说明，并在每轮工作开始时要求 Agent 输出：

```text
当前模式：
项目阶段：
本轮交付物：
验收标准：
最小垂直切片：
角色安排：
风险与验证：
暂不处理：
```

## 发布扫描边界

`scripts/scan_public_repo.py` 只用于本仓库发布前自检，不属于项目协作协议，也不会由初始化器分发到目标项目。它要求在 Git 工作树中运行并且只读取已跟踪文件；不会在 Git 缺失时递归扫描，因为那可能误读被忽略的本地凭据、构建产物和私有文件。目标项目应根据自身托管平台和安全要求配置独立的密钥扫描。

## 明确边界

- 当前公开版本不宣称对所有 Agent 一键安装。
- Codex 当前只声明记录中明确覆盖的本机有限验证，不外推到其他账户、版本或平台表面。
- 初始化器只操作用户明确指定的本地项目目录。
- 核心初始化器不依赖外部记忆服务；`meminit` 只在明确选用时调用本地 `pjm`，不配置 MCP、后台 watcher 或跨项目继承。
- 不同平台的多 Agent、权限和部署能力不应被假设为等价。

## 后续适配建议

后续可以按独立垂直切片增加 Codex Plugin、Claude Code、WorkBuddy 和通用 Prompt 包；Codex 配置适配不等于 Codex Plugin。每个适配器都应包含安装方法、卸载方法、最小演示和兼容性测试。
