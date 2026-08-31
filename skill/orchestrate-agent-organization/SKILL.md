---
name: orchestrate-agent-organization
description: Run a persistent, human-led AI studio that clarifies ideas, selects finite investment horizons, stewards products across tasks, uses reality evidence to continue/pause/retire work, and executes authorized projects through an automatically sized multi-agent organization. Use for new products or material features, cross-project portfolio decisions, operating-product ownership, long-term maintenance/retirement, capability learning, or complex projects needing governed subagents. Do not use for small or tightly sequential tasks that one agent can complete efficiently.
---

# Orchestrate an Agent Organization

Run one lead agent as the accountable organization steward. When work spans opportunities, products, projects, or invocations, preserve a Studio Kernel containing portfolio state, finite investment horizons, Product Assets, durable responsibility seats, reality evidence, and capability calibration. For an idea, new product, material feature, or ambiguous strategic change, first operate as the human's Founder Partner: discuss and clarify the product, create a decision-ready Founder Charter, and wait for explicit human authorization before material execution. Treat roles as logical seats and agent instances as leased elastic compute. Build a company operating system that converts model capability into durable product stewardship: selection, delivery, independent challenge, safe change, integration, operations, maintenance, retirement, and learning. Let the human shape values, goals, product/design choices, strategic boundaries, and material decisions. Make the machine control plane responsible for reversible investigation, portfolio recommendations inside the mandate, task scoring, organization topology, agent count, concurrency, token tier, leases, spawn quotas, and scale-up/scale-down decisions. Optimize durable outcome and organizational fitness; treat tokens as one constraint, not the objective.

## Route before loading heavy governance

Start with a lightweight machine preflight. Detect `studio_scope` when the request selects among projects, affects an operating Product Asset, must survive this task, changes investment, requests scale/pause/retire, or learns across projects. For studio scope, locate `STUDIO_STATE.json` or initialize it from `assets/studio-state.template.json`, read `references/studio-kernel.md`, and run the portfolio planner before creating an execution task graph. Then detect whether Founder discovery is required. Set `founder_discovery_required` and `founder_charter_status`; before `authorized`, sketch only reversible discovery, design, control, and verification work. Build only the minimum allowed task sketch needed for capacity planning, assign `decision_level`, and obtain an authoritative runtime snapshot. When child-agent tools are available, call the runtime's agent-list operation and pass the names of every currently active agent as `runtime_active_agents`; do not hand-count or infer occupancy. Use only the allowlisted source identifier accepted by the planner. Take the immutable active limit from runtime instructions or an exposed runtime limit. If no authoritative snapshot is available, omit agent names, label the source `unspecified`, and conservatively allow at most one new child.

Run the platform-native planner:

```text
powershell -File scripts/plan_portfolio.ps1 STUDIO_STATE.json # Windows studio scope
<python-executable> scripts/plan_portfolio.py STUDIO_STATE.json # other hosts, studio scope
powershell -File scripts/plan_capacity.ps1 capacity.json   # Windows
<python-executable> scripts/plan_capacity.py capacity.json # other hosts
```

On Codex desktop, call the workspace-dependency locator when Python is needed but unavailable on `PATH`. Do not manually reproduce the formula while either bundled implementation can run.

Honor the returned `execution_route`:

- `direct`: keep zero children, skip the governance and contract references, execute and verify locally, and record only the compact route result. Do not create an Intent Brief or organization artifacts.
- `governed-serial`: read the rules below and apply the assurance/control roles serially.
- `organized`: read the rules below before activating a child.
- `founder-discovery`: load `references/founder-office.md`, conduct adaptive human dialogue through one Founder Partner, and permit only reversible pre-authorization work. Do not activate implementation.
- `human-gated`: present the blocking decision and do not activate children until the gate is resolved.

All routes inherit the compact `company-v5` rules: preserve human root authority, serve product outcomes, tell the evidential truth, reuse safely before building, own the full lifecycle, keep artifacts navigable, cohesive, and economical, manage bounded context, challenge unsupported claims, isolate writes, preserve persistent stewardship, use least authority, preserve state, and prefer reversible change.

For every route except `direct`, read these five core files completely:

- `references/company-constitution.md` for binding employee rules, reuse policy, and definition of done.
- `references/organization-architecture.md` for the first-principles company topology, product lifecycle, state system, and fitness criteria.
- `references/cognitive-modes.md` for role-specific thinking procedures and lifecycle-stage routing.
- `references/governance.md` for human control, decision levels, permissions, self-modification, and escalation.
- `references/contracts.md` for intent briefs, organization plans, agent charters, decision packets, change packets, and cost telemetry.

Load only the task-specific heavy references:

- read `references/founder-office.md` for `founder-discovery`, any new product or material feature, ambiguous product intent, or a human request to clarify/design before building;
- read `references/studio-kernel.md` for cross-project selection, persistent product stewardship, operating evidence, investment, scale/pause/retire, or capability calibration;
- read `references/engineering-system.md` for software, repository, artifact-heavy, maintenance, debug, integration, release, or project-navigation work.
- read `references/integration-gate.md` whenever independent review returns findings, a material incident/change reaches final synthesis, or live operating obligations could be lost during compression.

Validate charters with `scripts/validate_charter.ps1` on Windows or `scripts/validate_charter.py` elsewhere before every activation, not only for elevated permissions. After validation, bind the child's actual working directory and tools to the declared isolated worktree; a JSON field alone is not isolation. If neither implementation can run, do not delegate write/spawn authority; validate read-only work manually and disclose the missing deterministic check.

## Preserve the control hierarchy

Apply these invariants throughout the task:

1. The human is the root authority and may participate, redirect, pause, reject, or take over at any time.
2. The lead agent retains end-to-end responsibility even after delegation.
3. Never ask the human to choose agent count, token tier, concurrency, spawn depth, lease length, or internal budget allocation. Infer them from the task graph and runtime state.
4. Child permissions must be a subset of the parent's delegable permissions.
5. Delegated budgets must remain within the machine-derived organizational envelope and any pre-existing root constraint.
6. A proposer must not be the sole approver, deployer, and auditor of a material change.
7. Keep decision and change records append-only; never conceal failed work.
8. Prefer reversible actions, narrow permissions, leases, sandboxes, staged rollout, and rollback.
9. Never create an agent merely to imitate a department, attend a simulated meeting, or restate another agent's work.
10. Bind every child and descendant to the parent's `company_policy_version`; require a machine-selected `lifecycle_stage`, `cognitive_mode`, `context_budget_units`, `artifact_budget_units`, scoped `context_sources`, and `learning_authority` in every charter.
11. A new product, material feature, or ambiguous strategic change must reach an explicitly human-authorized Founder Charter before implementation intended for integration begins.
12. A write-capable child must use a runtime-issued isolated worktree and a non-overlapping scoped write claim; never let two agents write the same shared workspace.
13. A project may close and an Agent lease may end, but affected Studio State, Product Asset responsibility, operating obligations, evidence freshness, stop conditions, and next review trigger must persist.
14. Founder authorization permits a product direction; it does not force portfolio investment. A studio-scoped build additionally requires a selected finite investment horizon, and a triggered stop condition can pause it despite sunk effort.

## Execute the workflow

### 0. Complete Studio, Founder, and machine routing

Classify the request first. A bounded task under existing authority may continue normally. Studio-scoped work first loads persistent state and receives a portfolio recommendation such as `discover`, `fund`, `continue`, `scale`, `revalidate`, `resume-review`, `pause`, `retire-review`, `reject`, `human-gated`, `queue`, or `retain-retired`. Apply hard gates and existing-user/maintenance/retirement obligations before relative ranking. Record the accountable decision and update Studio State; do not treat the heuristic score as ROI or authorization. Only an allowed finite horizon proceeds to Founder and capacity routing.

An idea, new product, material feature, ambiguous product direction, or explicit request to discuss/design first enters the Founder Office. Build the allowed task sketch, collect the runtime snapshot, run the applicable planners, and follow their results before creating organization prose. A direct task-local route ends the organizational workflow here only if no Studio State is affected. For all other routes, expand the sketch into the full task graph after loading the routed operating rules.

When the route is `founder-discovery`, use `references/founder-office.md`. Let the human narrate naturally; distinguish evidence, preference, inference, assumption, recommendation, decided, and undecided. Use only the reasoning lens that reduces the live uncertainty. Ask one or a few high-leverage questions, summarize changes each round, and draft the versioned Founder Charter. Adviser agents are optional machine-sized cells, not a human-facing committee. Before explicit `authorized` state, do not create build or integration-ready work. Re-run the portfolio planner after authorization for studio scope, then run the capacity planner only for a selected horizon.

### 1. Open human participation

After any required Founder Charter reaches `authorized`, or immediately for work that did not require it, share a concise Intent Brief containing:

- desired outcome and known non-goals;
- assumptions and unresolved choices;
- 2-3 meaningful design options when a real choice exists;
- risk, permission, and external-effect boundaries;
- the product, design, value, or risk decisions open to the human;
- the next reversible action.

Invite steering without creating an unnecessary blocking gate. Continue under explicit assumptions when the decision is reversible and inside the active Charter or mandate. Stop for the Founder authorization gate and the mandatory human gates defined in `references/governance.md`.

After the human-facing brief, report the machine-selected route, topology, child count, token tier, and rationale as transparency, not as questions. Treat every later human message as a control-plane event. Re-evaluate the goal, plan, permissions, current children, and pending decisions immediately. A human override supersedes prior agent decisions.

### 2. Build a task graph before an organization chart

Decompose only the portfolio-selected finite horizon into deliverables and dependencies. Mark each work item with:

- owner and acceptance criteria;
- complexity from 1-5;
- risk from 0-4;
- whether it is genuinely independent and parallelizable;
- required context, tools, permissions, and estimated effort units;
- interface coupling, context-isolation value, specialist need, critical-path value, and separation-of-duties requirement;
- lifecycle stage and the cognitive mode best suited to the work;
- downstream consumers and integration owner.

Assign these scores yourself from the available evidence. Do not ask the human to grade complexity, risk, effort, parallelism, or context size.

Define logical roles for strategy, product, architecture, implementation, assurance, operations, and audit as needed. Do not instantiate each role. Combine compatible low-load roles in the lead; split roles only for parallel capacity, context isolation, specialist tools, or separation of duties.

Map the task graph onto the logical company layers in `references/organization-architecture.md`. Keep product/program ownership, mission delivery, functional standards, assurance, and shared state distinct even when the lead temporarily occupies several seats.

For build, feature, maintenance, and debug work, add every applicable downstream lifecycle item before sizing: reuse research, compatibility impact, implementation, tests/evals, data or configuration migration, integration, release/rollback, observability/runbooks, support ownership, maintenance, and retirement. Initial code generation is one work item, not the project definition.

For a new project or material cross-boundary change, add architecture and project-map work before implementation. Use the navigation-first protocol in `references/engineering-system.md`. Do not solve context limits by producing a monolith, and do not mechanically fragment code by line count; split around responsibilities, contracts, ownership, test seams, and change patterns.

### 3. Calculate bounded capacity

Default to zero children, inspect the runtime's current active-agent capacity, and then let the machine select the smallest useful organization with positive organizational value. Create children only when at least one condition holds:

- two or more concrete workstreams can progress independently;
- an independent evaluator is justified by material risk;
- a workstream needs isolated context or a distinct tool/model capability;
- a bounded mission subtree has enough independent work to justify its own internal loop.
- focused context, specialist capability, critical-path reduction, interface ownership, or separation of duties outweighs coordination cost.

Do not spawn for vague consultation, strongly sequential work, tiny edits, duplicated review, or a task whose acceptance criteria remain unknown.

For studio scope, run the portfolio planner first; it answers whether the next horizon should proceed and what envelope is available. Then prepare a capacity input with active-agent names from the latest authoritative snapshot and run the capacity planner; it answers how to execute that allowed horizon. The capacity planner compares token economics, reasoning-quality gains, context isolation, specialist needs, critical-path latency, control value, assurance, and coordination cost. It chooses the route, topology, active child count, worker/verifier split, and relative token allocation. Use its child count as a ceiling, not a target. A worker may be justified even when it adds tokens if its quality, latency, specialist, interface, or control value is higher; report that premium explicitly. Cap the result by the selected portfolio envelope, discovered runtime concurrency, and immutable root policies, not by asking the human to configure a budget. Keep one slot for the lead. Prefer reusing a completed child with a follow-up task over creating another instance.

Refresh the authoritative active-agent list immediately before every spawn. Stop spawning when the new snapshot has no free slot, even if an earlier plan allowed more. Spawn sequentially so each successful activation is visible to the next snapshot. If another task consumes a slot concurrently, reduce the organization instead of racing it.

Re-run capacity planning automatically when the task graph changes, a human changes direction, a child completes, a queue grows, verification discovers new work, or coordination overhead rises. Scale down immediately when marginal value falls below cost.

### 4. Charter every activated child

Give each child one bounded mission using the Agent Charter and Task Contract in `references/contracts.md`. Include:

- a concrete artifact or decision to return;
- original evidence and exact scope;
- acceptance criteria and exclusions;
- machine-selected permissions, token tier, relative token allocation, lease, and stop conditions;
- reporting format and integration owner;
- whether it may propose or create children.
- inherited `company_policy_version`, machine-selected `lifecycle_stage`, and one primary `cognitive_mode` from `references/cognitive-modes.md`.
- a Context Capsule with machine-selected `context_budget_units`, `artifact_budget_units`, non-empty scoped `context_sources`, project-map nodes, invariants, evidence duties, checkpoint triggers, and `learning_authority`.
- an authoritative active-agent roster, an authorized active `auditor_id`, and whether assurance is parent-accountable or independent.
- `write_scope_mode`, repository-relative `write_scope`, and runtime-issued `workspace_id`; use `read-only`, an empty scope, and `none` when no workspace write is granted.
- for studio scope, the portfolio item/Product Asset IDs, durable owner seat, finite horizon, reality-evidence duties, and exact Studio State update destination.
- the exact parent-Charter path, child-Charter path, validator command, and runtime-roster source used for this activation. For a descendant, never infer its validation parent from the current Agent's own child Charter; use the explicit descendant-parent validation artifact.

Use minimal context. Prefer a clean context plus a complete task packet instead of full-history forks. Never assign two children the same open-ended task unless independent comparison is intentional and budgeted.

Each child must orient from the project map, maintain a small evidence/assumption/decision ledger, checkpoint at milestones, and compact/rebase when its context becomes broad, stale, repetitive, or contradictory. Require a distilled handoff; do not accept a raw transcript or log dump as integration input.

Send the compact constitution binding and only the selected cognitive-mode instructions to the child. For code/design review, default to `adversarial-review`; for make/buy/reuse, default to `reuse-first-research`; for bugs and incidents, default to `debug-and-incident`; for existing-system evolution, include `maintenance-stewardship` as the primary or counter-mode.

Children may create descendants only when their charter has a positive machine-assigned `spawn_quota`. Require them to build a local task graph, run the same capacity calculation against current runtime state, preserve the global active-agent and creation budgets, and pass the same charter rules to descendants. Otherwise instruct them to submit the local task graph to the lead, which decides automatically whether to create another child.

### 5. Operate through artifacts and triggered decisions

Use the Founder meetings in `references/founder-office.md` only when a live decision, challenge, authorization, or milestone feedback loop requires human interaction. Every such meeting has an exit criterion and updates one canonical artifact. Never simulate recurring status meetings, voting committees, or attendance roles.

Use a centralized control plane:

- the lead maintains goal, task graph, budgets, decisions, risks, and integration state;
- mission children produce artifacts or evidence;
- functional reviewers apply standards;
- assurance children try to falsify claims;
- the human sees material forks, risks, and external actions.
- Studio State preserves portfolio, Product Asset, evidence, responsibility, and capability changes beyond the current task.

Allow direct child-to-child communication only when it removes a concrete dependency. Record the resulting decision or artifact centrally. Avoid all-to-all chatter.

Enforce artifact economy from `references/engineering-system.md`: assign one normative home per fact, link instead of restating, place current status above append-only history, and require justification before exceeding a charter's `artifact_budget_units`. A reviewer normally writes a bounded finding set into one assurance artifact rather than duplicating every producer document.

Share brief progress updates at meaningful milestones. Include what changed, what decision is open, what children are active, and whether the human can still alter the path. Do not require the human to wait for the final result to participate.

### 6. Make and modify decisions safely

Classify decisions using D0-D5 from `references/governance.md`. Use one accountable decision owner; add independent challenge as uncertainty, impact, or irreversibility increases.

For changes to code, prompts, models, organization, policy, permissions, evaluation, or budgets:

1. create a Change Packet;
2. map affected components and invariants;
3. test in a sandbox, replay, or shadow path;
4. obtain the required approval and independent check;
5. roll out narrowly;
6. monitor success and failure thresholds;
7. commit or roll back;
8. update the project map or other organizational memory through the governed learning protocol.

Never let an agent unilaterally change its own permissions, budget ceiling, evaluator, audit trail, or approval rules.

### 7. Integrate and verify

The lead, not the children, owns the final synthesis. Check:

- every deliverable against its acceptance criteria;
- interfaces and assumptions between workstreams;
- contradictions, duplicated work, and missing scope;
- whether local artifacts compose into the product outcome and whether interfaces have one accountable owner;
- absolute claims against their failure scope, producer-controlled evidence, and unbounded cross-system barriers;
- deterministic tests and external evidence where available;
- security, privacy, cost, maintainability, and rollback proportional to risk;
- whether human changes were incorporated.
- whether reuse was investigated with provenance/license/security evidence and whether the full lifecycle definition of done is satisfied.
- whether architecture/navigation stayed accurate, code remained cohesive, comments explain contracts or non-obvious reasons, and every child returned a valid context handoff.
- whether discovered techniques remain Learning Candidates or have traceable approval before entering project or Skill memory.
- whether duplicate summaries were consolidated, canonical facts have one owner, current verdicts are unambiguous, and artifact budgets were respected.
- whether every affected live Product Asset retains a compact Operating Control Packet: durable/on-call owner, financial reconciliation control when money is affected, support surface, decision SLIs and alerts, incident/safe-state route, maintenance envelope, retirement condition, and next reality-evidence trigger. Under an output limit, link to the canonical packet instead of silently dropping these controls.
- whether an evaluator judging organization feasibility received the frozen runtime active limit, authoritative roster/occupancy, available slots, and actual activated topology. Blind identities when useful, but do not hide capacity facts that determine executability.

Use an independent verifier for material risk. Do not treat agent consensus as evidence.

Before final delivery, freeze the independent finding, affected-subject, accountable-owner principal, authority, applicability, authorized-verifier, and evidence catalog in `assurance-v1` using `assets/assurance-manifest.template.json`. Evidence attestations use `assets/evidence-attestation.template.json`; their files and artifacts stay beside the manifest under relative non-reparse paths so validators can recompute their digests. Record the manifest SHA-256 in a parent Charter or Founder/assurance decision outside the producer/integrator write scope. Bind the complete synthesis to the same manifest in `integration-v2` using `assets/integration-packet.template.json`. Run `scripts/validate_integration.ps1 packet.json manifest.json <trusted-manifest-sha256>` on Windows or `scripts/validate_integration.py packet.json manifest.json <trusted-manifest-sha256>` elsewhere after review import, after synthesis changes, and once more immediately before delivery. Never derive the trusted argument from the caller-supplied manifest during that integration step. Reject an invalid synthesis. When valid but a subject is not allowed to advance, deliver only its explicit safe decision and blockers. Use the validator-generated canonical delivery Markdown or link its digest; do not manually compress it into a readiness claim.

### 8. Scale down and close

Release or stop children as soon as their mission completes, blocks, duplicates another stream, or loses expected value. Do not keep idle departments alive. Before dissolving a studio-scoped mission cell, atomically update its portfolio state, Product Asset stewardship, reality evidence/freshness, operating obligations, stop conditions, capability candidates, and next event-driven trigger. Archive useful decisions and evidence, not full conversational noise. Promote only approved learning to the project map, Studio capability registry, tests, runbooks, standards, or a versioned Skill update; expire task-only memory.

Report:

- outcome and remaining risks;
- organization actually activated versus logical roles left dormant;
- important decisions and human interventions;
- verification performed;
- children created, reused, or stopped and why;
- whether the coordination/token spend was justified;
- the machine-selected capacity and token tier and any automatic replanning;
- measured wall-clock interval, child activations/reuse, coordination actions, and rework cycles;
- actual model-token usage only when the runtime exposes it; otherwise report `unavailable` and keep planned token weights clearly labeled as estimates;
- safe next actions.

## Use child-agent tools carefully

When child-agent tools are available:

- inspect live capacity before spawning;
- spawn only the machine-selected number produced by the capacity plan;
- never activate a write-capable child until its runtime-issued isolated worktree exists and its actual working directory is bound to that workspace;
- use minimal history propagation when the task packet is self-contained;
- wait for meaningful results instead of repeatedly polling;
- send follow-up work to an existing suitable child;
- interrupt work that has become obsolete after human steering;
- never create user-owned threads as a substitute for internal children.

When child-agent tools are unavailable, execute the same decision and assurance roles serially and state that no independent child execution occurred.
