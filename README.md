# 和 Agent 一起做项目：从模糊想法到稳定交付

> 一套可以安装、迁移和持续迭代的人机项目协作章程。

`agent-project-playbook` 帮助没有完整技术背景的人与 AI Agent 一起推进项目。用户可以只描述想法、感受和阻力，并且只需要与主 Agent 保持一条对话线；主 Agent 负责判断项目阶段、选择本轮交付物、形成问题单、组织后台专业能力、审查结果并完成交付。

当前版本：`v0.3.0`

## 核心工作流

```text
模糊想法
→ Design Thinking
→ 探索 / 启动 / 实施
→ 项目阶段判断
→ 本轮交付物
→ 问题单
→ 垂直切片
→ 主 Agent 托管执行
→ 测试、文档与交付闭环
```

一条项目主线由两个后台引擎支撑：

- 记忆引擎管理信息的作用范围、类型、可信状态和晋升路径。
- 编排引擎采用 Manager Pattern；主 Agent 先判断是否值得委派，再选择模型、推理和权限分离的执行配置，最后回收、审查并统一验收。

两台引擎不是并排工作的孤立模块。记忆为主 Agent 提供经过治理的长期上下文，
编排把执行结果、测试和反馈重新沉淀为候选记忆，形成：

```text
理解 → 编排 → 执行 → 验证 → 记忆 → 更好的理解
```

完整的三级记忆、跨层晋升、四期路线和抗模型变迁设计见
[`双引擎成长蓝图`](docs/EVOLUTION_BLUEPRINT.zh-CN.md)。

这里的 Bug、UI、体验、重构、性能、数据、测试和部署属于“切片级分类”，不会代替项目阶段判断。新项目也不会默认直接进入编码，用户无需自己判断该调用哪个 Agent。

完整协议保存在 `docs/`，不会整份复制进每个项目的 `AGENTS.md`。生成项目只安装精简路由规则，并在需要时加载项目生命周期、多 Agent 路由和项目文档三个本地 Skill。

## 快速开始

克隆仓库后，普通本地项目先运行统一入口。默认是中文 `simple` 配置，并尝试安装安静模式 projectmem；dry-run 不写文件：

```bash
bin/meminit /path/to/your-project your-project
```

确认报告后再安装：

```bash
bin/meminit /path/to/your-project your-project --apply
```

`meminit` 默认加入 Playbook 文件和可选的 projectmem 冷记忆适配器。该适配器关闭 watcher、Git hooks、历史回填、全局继承、自动捕获和 MCP 配置；没有安装 `pjm` 时，可加 `--without-projectmem` 只安装核心 Playbook。

初始化器不会覆盖已有的 `AGENTS.md`、项目文档、本地 Skill 或 `.projectmem`。任一目标路径存在时，安装前检查会停止写入并要求人工合并，避免形成两套混合规则。

默认 `simple` 配置面向本地、单用户、低风险项目，不安装生产安全脚本。当前证据确认存在真实运行、共享状态、真实用户或外部写入时，使用 `production` 配置：

```bash
bin/meminit /path/to/your-project your-project --production
```

已有项目只生成升级比较，不覆盖任何文件：

```bash
bin/meminit /path/to/your-project --upgrade
```

每次新安装都会写入 `.agent-playbook.toml`，只记录 Playbook 版本、配置和语言，供后续升级检查使用。

需要英文项目文档时增加 `--locale en`。核心初始化器仍可单独运行，且不依赖 projectmem：

```bash
python3 scripts/init_project.py /path/to/your-project --project-name your-project --locale zh-CN
```

稳定 checkout 可以显式激活为当前用户的唯一入口。该操作默认也只显示计划：

```bash
python3 scripts/activate_user_entry.py --playbook-root /path/to/agent-project-playbook
```

## 仓库内容

- [`docs/PROTOCOL.zh-CN.md`](docs/PROTOCOL.zh-CN.md)：完整协作章程和项目主线。
- [`docs/EVOLUTION_BLUEPRINT.zh-CN.md`](docs/EVOLUTION_BLUEPRINT.zh-CN.md)：双引擎成长闭环、三级记忆和四期演进路线。
- [`docs/MEMORY_MODEL.zh-CN.md`](docs/MEMORY_MODEL.zh-CN.md)：项目记忆的范围、类型、可信状态和晋升规则。
- [`docs/ORCHESTRATION_MODEL.zh-CN.md`](docs/ORCHESTRATION_MODEL.zh-CN.md)：主 Agent 托管、模型分层、委派和验收规则。
- [`docs/CODEX-ADAPTER.zh-CN.md`](docs/CODEX-ADAPTER.zh-CN.md)：Sol、Terra、Luna 的 Codex 配置与运行规则。
- [`docs/CODEX-E2E-2026-07-25.md`](docs/CODEX-E2E-2026-07-25.md)：本机 Codex 配置与模型路由验证证据。
- [`docs/PORTABILITY.zh-CN.md`](docs/PORTABILITY.zh-CN.md)：Codex、其他 Agent 和通用提示词的适配边界。
- [`templates/`](templates/)：精简项目规则、蓝图、架构、当前交接、三个默认 Skill 和一个 production 专用 Skill。
- [`skills/agent-project-bootstrap/`](skills/agent-project-bootstrap/)：可复用的项目启动 Skill。
- [`bin/meminit`](bin/meminit)：面向用户的统一 dry-run / apply / upgrade 入口。
- [`scripts/init_project.py`](scripts/init_project.py)：支持 simple/production 配置、默认 dry-run 和只读升级检查的初始化器。
- [`adapters/projectmem/`](adapters/projectmem/)：可选的安静模式项目冷记忆适配器。
- [`adapters/codex/`](adapters/codex/)：Codex 用户级 Bootstrap Skill 的唯一源文件。
- [`scripts/project_safety.py`](scripts/project_safety.py)：production 配置的可选 worktree 辅助工具；不部署、不推送，也不输出内部版本标识。

CI 会直接检查中英文模板、统一入口、可选适配器、初始化分发契约、记忆与编排模型契约、Docs Lint、Ruff
和公开文件敏感模式。敏感扫描只读取 Git 跟踪文件，允许 `example.com`
等保留示例邮箱域名。`scan_public_repo.py` 是本仓库的发布自检工具，需要 Git，
且不会随初始化器安装到目标项目；生成项目应按自己的发布流程配置密钥扫描。

## 设计原则

1. 用户不需要先学会给任务分类或管理多个 Agent。
2. 每轮只推进一个可独立验收的垂直切片。
3. 主 Agent 是唯一责任入口，负责路由、审查、验证和最终交付。
4. `NO_DELEGATION` 是正常路由结果；基础任务不为展示多 Agent 而拆分。
5. 当前证据高于历史记忆，项目之间保持隔离。

## 兼容性

核心章程不依赖具体模型；`ORCHESTRATION_MODEL.zh-CN.md` 中的 Sol、Terra、Luna 是当前 Codex 映射，不代表其他平台具有同名能力。Codex 省心模式已完成本机配置加载、显式 Luna/Terra 路由和主 Agent 复核 smoke；验证范围与已知上限见 [E2E 记录](docs/CODEX-E2E-2026-07-25.md)。Claude Code、WorkBuddy 适配器尚未提供，不能宣称支持。详见[可移植性说明](docs/PORTABILITY.zh-CN.md)。

## 参与迭代

这个仓库会随着真实项目协作持续更新。建议把新增规则写成可验证的问题：它解决了什么混乱、触发条件是什么、如何判断它真的有效。提交方式见[参与贡献](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
