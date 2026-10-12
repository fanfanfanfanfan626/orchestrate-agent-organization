# Try the planners in five minutes

Download or clone this repository. No account, API key or dependency install is needed for these two commands (Python 3.10+):

```sh
python skill/orchestrate-agent-organization/scripts/plan_portfolio.py skill/orchestrate-agent-organization/assets/first-trial-studio.json
python skill/orchestrate-agent-organization/scripts/plan_capacity.py skill/orchestrate-agent-organization/assets/first-trial-capacity.json
```

Expected: the idea stays in `discovery`; capacity reports `runtime_snapshot_authoritative: false` and at most one child. These fictional examples print a plan, not authorization or execution. They do not create agents, modify files, install tools or publish anything. [Windows commands and interpretation](skill/orchestrate-agent-organization/references/first-trial.md).

中文：先体验两个只读规划器，不用安装 Skill 或登录。一个判断是否应该继续探索，一个估计任务怎样分配。不是自动组建公司，也不能把计划当成真实用户证据。
