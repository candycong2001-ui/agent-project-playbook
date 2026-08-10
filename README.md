# Agent Project Playbook

> 一套面向普通用户的可安装项目协作骨架：你只描述目标，主 Agent 负责收敛、实施、验证和交付。

当前版本：`v0.3.1`

## 它解决什么

- 不要求用户先学会写完整需求、拆任务或管理多个 Agent。
- 用精简 `AGENTS.md` 和按需 Skills 约束工作方式，避免全局提示词持续膨胀。
- 用 BLUEPRINT、ARCHITECTURE、CURRENT_HANDOFF 固定项目文档节奏。
- 把 projectmem 限定为项目冷记忆；当前代码、测试和真实输出始终优先。
- 普通本地项目保持轻量，只有真实生产运行面才增加发布门禁。

## 快速开始

克隆仓库：

```bash
git clone https://github.com/candycong2001-ui/agent-project-playbook.git
cd agent-project-playbook
```

新项目先做 dry-run，不写文件：

```bash
bin/meminit /path/to/your-project your-project
```

确认没有冲突后安装：

```bash
bin/meminit /path/to/your-project your-project --apply
```

旧项目只生成升级比较，不覆盖现有内容：

```bash
bin/meminit /path/to/your-project --upgrade
```

常用选项：

- `--production`：增加按影响面工作的生产发布 Skill。
- `--without-projectmem`：不安装可选的 projectmem 适配器。
- `--locale en`：生成英文项目文档；默认中文。

`meminit` 不覆盖已有 `AGENTS.md`、项目文档、Skills 或 `.projectmem`。projectmem 默认关闭 watcher、Git hooks、历史回填、全局继承、自动捕获和 MCP 配置。

## 安装后的项目

```text
项目根目录
├── AGENTS.md                         # 当前项目薄路由
├── docs/
│   ├── BLUEPRINT.md                 # 做什么
│   ├── ARCHITECTURE.md              # 怎么组成
│   └── CURRENT_HANDOFF.md           # 现在做到哪里
├── .agents/skills/                  # 按需工作流程
├── .agent-playbook.toml             # 版本、语言和配置
└── .projectmem/                     # 可选项目冷记忆
```

`simple` 默认安装项目生命周期、多 Agent 路由和 Docs Lint。`production` 额外安装生产发布门禁；projectmem 启用时额外安装项目冷记忆 Skill。

## 工作方式

1. 模糊想法先探索，不急着创建文件或写代码。
2. 准备落地时确定本轮交付物和最小可验证闭环。
3. 主 Agent 按需调用本地 Skills 或子 Agent，并负责最终复核。
4. 交付前运行相关测试；重要工作同时更新当前交接并运行 Docs Lint。

当前证据高于历史记忆，项目之间不继承实现状态、凭据或失败经验。

## Codex 用户入口

稳定 checkout 可以激活全局 `meminit` 和 Bootstrap Skill。命令默认只显示计划：

```bash
python3 scripts/activate_user_entry.py --playbook-root "$PWD"
```

确认后增加 `--apply`；需要同时安装精简的 Codex 全局 `AGENTS.md` 时，再增加 `--with-global-agents`。旧全局文件会保留一份备份。

## 深入阅读

- [完整协作协议](docs/PROTOCOL.zh-CN.md)
- [项目记忆模型](docs/MEMORY_MODEL.zh-CN.md)
- [主 Agent 编排模型](docs/ORCHESTRATION_MODEL.zh-CN.md)
- [Codex 适配层](docs/CODEX-ADAPTER.zh-CN.md)
- [双引擎演进蓝图](docs/EVOLUTION_BLUEPRINT.zh-CN.md)
- [平台兼容边界](docs/PORTABILITY.zh-CN.md)

仓库使用单元测试、双语 Docs Lint、Ruff 和公开文件扫描验证分发契约。贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
