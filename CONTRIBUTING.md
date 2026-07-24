# 参与贡献

感谢你帮助完善这套人机项目协作章程。贡献不要求宏大；一个被真实项目验证过的小规则，比一套没有证据的大框架更有价值。

## 1. 先写清问题

提交 Issue 或 PR 前，请明确：

- 当前证据：实际发生了什么。
- 推断问题：现有规则为什么没有避免它。
- 验收标准：怎样证明改进有效。
- 最小切片：本次只改什么。
- 暂不处理：哪些相关问题留到以后。

## 2. 本地验证

需要 Python 3.10 或 3.11，以及 Ruff 0.16.0。可以在独立虚拟环境中安装 Ruff：

```bash
python3 -m pip install ruff==0.16.0
```

然后运行以下验证：

```bash
python3 -m unittest discover -s tests -v
python3 templates/skills/project-docs/scripts/docs_lint.py --project-root templates --language en
python3 templates/skills/project-docs/scripts/docs_lint.py --project-root templates/zh-CN --language zh-CN
python3 scripts/scan_public_repo.py
ruff check .
ruff format --check .
```

仓库 CI 会在 Ubuntu 和 macOS、Python 3.10 和 3.11 上重复这些检查。

## 3. 模板与语言

- `templates/` 是英文模板。
- `templates/zh-CN/` 是中文模板。
- 修改任一必需标题时，必须同步 `docs_lint.py` 中对应语言的 `RULES`。
- 契约测试会比较所有模板二级标题与 `RULES`，避免静默漂移。
- 机器路径、Skill 名称和命令保持英文，不翻译代码标识。

## 4. 兼容性声明

- 单元测试通过只代表分发契约通过，不代表目标 Agent 平台端到端兼容。
- 声明某个平台“支持”前，必须记录平台、版本、日期、安装步骤和实际结果。
- 未经真实 E2E 验证的平台应标记为“布局约定”或“未验证”。

## 5. 提交边界

- 一次 PR 只解决一个可以独立验收的问题。
- 不提交个人路径、真实邮箱、凭据、私有项目名、运行日志或会话历史。
- 不为顺手优化扩大当前切片。
- 用户可见变化需要同步 README、协议或可移植性说明。
