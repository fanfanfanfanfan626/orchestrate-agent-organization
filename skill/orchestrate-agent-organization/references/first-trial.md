# Five-minute first trial

You can try the deterministic planners without installing a Skill or connecting an AI account. They print JSON; they do not create agents, write project state, grant authority or release software. These fictional fixtures are not proof of product demand or authorization. Real Skill use still requires reading SKILL.md and the routed references.

From the unpacked `orchestrate-agent-organization` directory, with Python 3.10+:

```sh
python scripts/plan_portfolio.py assets/first-trial-studio.json
python scripts/plan_capacity.py assets/first-trial-capacity.json
```

Or on Windows with PowerShell:

```powershell
powershell -NoProfile -File scripts/plan_portfolio.ps1 assets/first-trial-studio.json
powershell -NoProfile -File scripts/plan_capacity.ps1 assets/first-trial-capacity.json
```

Expect the portfolio planner to keep the raw idea in reversible `discovery`, not fund implementation. The capacity planner reports `runtime_snapshot_authoritative: false` and recommends at most one child. A hand-written roster is not runtime evidence; never relabel one as `collaboration.list_agents`. Only use an allowlisted authoritative source when that tool actually returned the snapshot. The planner recommends allocation but does not enforce a sandbox.

What to inspect next: change the fixture in a copy, reduce the active limit, rerun, and compare the recommendation. For real work, ask the assistant to assess whether the direct route is sufficient before making an organization.

## 中文入口

先运行这两个只读规划器，看它们怎样把未经确认的想法留在探索阶段、在缺少真实运行时信息时限制并发。它们不创建 Agent、不改文件，也不会替你授权。无需先读完全部治理文档就能体验 CLI；真正调用 Skill 时仍应按 SKILL.md 完整读取所需规则。
