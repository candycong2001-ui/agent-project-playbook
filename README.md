# 和 Agent 一起做项目：从模糊想法到稳定交付

> 一套可以安装、迁移和持续迭代的人机项目协作章程。

`agent-project-playbook` 帮助没有完整技术背景的人与 AI Agent 一起推进项目。用户可以只描述想法、感受和阻力；主 Agent 负责判断当前项目阶段、选择本轮交付物、形成问题单、切出可验收闭环，并组织所需专业能力完成交付。

当前版本：`v0.1.1`

## 核心工作流

```text
模糊想法
→ Design Thinking
→ 探索 / 启动 / 实施
→ 项目阶段判断
→ 本轮交付物
→ 问题单
→ 垂直切片
→ 角色分发
→ 测试、文档与交付闭环
```

这里的 Bug、UI、体验、重构、性能、数据、测试和部署属于“切片级分类”，不会代替项目阶段判断。新项目也不会默认直接进入编码。

## 快速开始

克隆仓库后，先做安全检查，不写文件：

```bash
python3 scripts/init_project.py /path/to/your-project --project-name your-project --locale zh-CN
```

确认报告后再安装：

```bash
python3 scripts/init_project.py /path/to/your-project --project-name your-project --locale zh-CN --apply
```

初始化器不会覆盖已有的 `AGENTS.md`、项目文档或本地 Skill。任一目标文件已存在时，整次安装都会保持零写入并要求人工合并，避免形成两套混合规则。

需要英文项目文档时，将 `--locale zh-CN` 改为 `--locale en`。为了兼容 `v0.1.0`，省略参数时仍默认英文。

## 仓库内容

- [`docs/PROTOCOL.zh-CN.md`](docs/PROTOCOL.zh-CN.md)：完整协作章程。
- [`docs/PORTABILITY.zh-CN.md`](docs/PORTABILITY.zh-CN.md)：Codex、其他 Agent 和通用提示词的适配边界。
- [`templates/`](templates/)：项目规则、蓝图、架构、当前交接和文档维护 Skill。
- [`skills/agent-project-bootstrap/`](skills/agent-project-bootstrap/)：可复用的项目启动 Skill。
- [`scripts/init_project.py`](scripts/init_project.py)：默认 dry-run、明确确认后才写入的便携初始化器。

CI 会直接检查中英文模板、初始化分发契约、Docs Lint、Ruff 和公开文件敏感模式。敏感扫描只读取 Git 跟踪文件，允许 `example.com` 等保留示例邮箱域名。

## 设计原则

1. 用户不需要先学会给任务分类。
2. 每轮只推进一个可独立验收的垂直切片。
3. 主 Agent 负责阶段判断、任务路由、整合和最终交付。
4. 当前代码、测试和真实运行证据高于历史记忆。
5. 不把一个项目的状态、凭据和失败经验自动带进另一个项目。

## 兼容性

核心章程与具体模型无关。当前版本的初始化器和中英文分发契约有自动化验证；Codex 的 `AGENTS.md` / Agent Skills 仅完成布局和结构验证，尚未完成真实平台端到端测试。Claude Code、WorkBuddy 适配器尚未提供，不能宣称支持。详见[可移植性说明](docs/PORTABILITY.zh-CN.md)。

## 参与迭代

这个仓库会随着真实项目协作持续更新。建议把新增规则写成可验证的问题：它解决了什么混乱、触发条件是什么、如何判断它真的有效。提交方式见[参与贡献](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
