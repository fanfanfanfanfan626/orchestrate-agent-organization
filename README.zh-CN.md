# Persistent AI Studio（持久化 AI 工作室）

[产品网页](https://fanfanfanfanfan626.github.io/orchestrate-agent-organization/) · [English](README.md) · [AI 安装说明](AI_INSTALL.md) · [参与贡献](CONTRIBUTING.md)

`orchestrate-agent-organization` 是一个面向 AI Agent 的组织编排 Skill。它让一个主 Agent 在人类掌握最终权力的前提下，选择值得推进的有限阶段、澄清和授权重大产品决策、按真实任务自动确定多 Agent 规模，并把产品责任、现实证据和运行状态延续到后续任务。

它优先适配 Codex，也可以迁移到具备本地 Skill、命令执行、持久化文件和子 Agent 生命周期工具的其他平台。

## 它解决什么问题

许多多 Agent 提示词先画组织架构，任务结束后所有责任和上下文也随之消失。这个 Skill 从实际工作出发，并保留真正需要延续的状态：

- Founder Office：先与人类澄清新产品或重大变更，再进入授权；
- Studio Kernel：管理跨任务的产品组合、产品资产和长期责任；
- Python 与 PowerShell 双实现的确定性组合规划、容量规划工具；
- 有边界的子 Agent 章程、权限、租期、预算和写入范围；
- 独立保证与无损集成门；
- 覆盖发现、交付、运营、维护和退出的完整生命周期。

## 在 Codex 中安装

真正可安装的 Skill 位于 [`skill/orchestrate-agent-organization`](skill/orchestrate-agent-organization)。仓库级说明文档刻意放在 Skill 本体之外。

### Windows PowerShell

```powershell
git clone https://github.com/fanfanfanfanfan626/orchestrate-agent-organization.git
$destination = Join-Path $env:USERPROFILE ".codex\skills\orchestrate-agent-organization"
New-Item -ItemType Directory -Force (Split-Path $destination) | Out-Null
Copy-Item ".\orchestrate-agent-organization\skill\orchestrate-agent-organization" $destination -Recurse
```

### macOS 或 Linux

```bash
git clone https://github.com/fanfanfanfanfan626/orchestrate-agent-organization.git
mkdir -p ~/.codex/skills
cp -R orchestrate-agent-organization/skill/orchestrate-agent-organization ~/.codex/skills/orchestrate-agent-organization
```

安装后重启 Codex，再明确调用：

```text
使用 $orchestrate-agent-organization，把这个产品想法变成由人类治理、可持续运行的 AI 工作室，并且只执行已经授权的有限阶段。
```

如果让另一个 AI 帮你安装，请把 [AI_INSTALL.md](AI_INSTALL.md) 交给它。

## 运行条件

核心治理材料都是普通 Markdown 和 JSON。完整运行还需要：

- 能加载 `SKILL.md` 及其相对路径资源；
- 能在本地保存 Studio State 和决策产物；
- Python 3.10+ 或 PowerShell 7+；
- 多 Agent 模式下具备列出、创建、通信、等待、中断和复用子 Agent 的能力；
- 给并发写入型 Agent 提供隔离工作区或 worktree。

如果平台没有子 Agent 工具，Skill 会把决策、执行和保证角色改为串行完成。其他平台的工具名可能不同，因此可能需要适配。

## 目录说明

| 路径 | 作用 |
| --- | --- |
| `SKILL.md` | 路由规则、控制层级和完整工作流 |
| `references/` | 公司宪法、治理、合同、Founder Office、Studio Kernel、工程和集成规则 |
| `scripts/plan_portfolio.*` | 校验 Studio State，并推荐有限的组合动作 |
| `scripts/plan_capacity.*` | 根据任务和运行时事实选择最小有效组织 |
| `scripts/validate_charter.*` | 校验授权、预算、层级、租期、隔离和保证绑定 |
| `scripts/validate_integration.*` | 把保证证据绑定到规范化交付包 |
| `assets/` | Studio State、保证、证据声明和集成 JSON 模板 |
| `agents/openai.yaml` | Codex 中显示和调用所需的元数据 |

Python 运行工具只依赖标准库；Windows 环境还提供对应 PowerShell 实现。

## 本地验证

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_release.py
```

验证器会检查包结构、frontmatter、UI 元数据、所有被引用文件、JSON 模板、Python 语法、命令入口，以及是否误带本机文件或生成文件。GitHub Actions 还会解析全部 PowerShell 脚本。

## 边界

- 它是 Agent 组织的操作系统，不保证决策一定正确，也不代替安全评审。
- Skill 规定的重大节点仍然必须由人类授权。
- 多个 Agent 同意不等于证据；仍然需要确定性测试和外部现实证据。
- 容量规划器是有边界的协调启发式，不是投资回报模型。

## 开源协议

MIT，见 [LICENSE](LICENSE)。

## 相关项目

- [Idea Council](https://github.com/fanfanfanfanfan626/challenge-and-refine-ideas)：在重大实施前澄清并反证想法。
- [Mastery Tutor](https://github.com/fanfanfanfanfan626/mastery-tutor)：为兼容的 AI Agent 提供本地优先的掌握式学习。
