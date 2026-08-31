# Engineering structure, context, and learning system

Use this system for software and other artifact-heavy projects. Its purpose is to make the organization legible to the next agent, reduce rediscovery, prevent architectural decay, and convert useful experience into governed institutional memory.

## 1. Architecture before material implementation

For a new project or a material cross-boundary change, first establish:

- product purpose, users, non-goals, and success evidence;
- bounded domains or subsystems and the owner of each contract;
- entry points, data/control flows, external dependencies, trust boundaries, and persistent state;
- interfaces, schemas, invariants, compatibility obligations, failure behavior, and rollback;
- test seams, observability, deployment path, operational ownership, and retirement path.

The architecture is a decision aid, not speculative ceremony. Record only the structure needed to make current changes safe and navigable. Prefer a small number of cohesive modules with explicit contracts over both a monolith and hundreds of meaningless fragments.

## 2. Project map and layered navigation

Maintain one canonical project map at `PROJECT_MAP.md` or `docs/project-map.md`. For very large repositories, the root map may link to module maps. The map is a navigation index, not a duplicate of all documentation. It must identify:

1. product purpose and current lifecycle status;
2. main entry points and common task routes;
3. subsystem/module tree with responsibilities and owners;
4. critical data and control flows;
5. public APIs, schemas, invariants, and compatibility boundaries;
6. external/runtime dependencies, configuration, secrets boundaries, and persistent stores;
7. test suites, fixtures, quality gates, and how to run the smallest relevant check;
8. observability, dashboards, logs, runbooks, migrations, release and rollback paths;
9. known risks, deprecated paths, and current architecture decisions;
10. links from map nodes to authoritative source files rather than copied prose.

An optional machine-readable `project-map.json` may index paths, tags, owners, dependencies, interfaces, and test commands when repository size justifies it.

For Codex projects, use a root `AGENTS.md` for repository-wide instructions and nested `AGENTS.md` files only when a subtree has genuinely different rules. Keep the root concise because closer instructions override broader ones. A project-specific reusable workflow may live under `.agents/skills/<name>/` with `SKILL.md`, `references/`, and `scripts/` when useful.

### Navigation-first protocol

Before broad search or code modification:

1. read the root project map;
2. identify the relevant map node and nearest applicable `AGENTS.md`;
3. load only the linked module map, interfaces, source, tests, decisions, and recent history needed for the mission;
4. verify map claims against the current repository;
5. update stale map entries in the same change or record a blocking discrepancy.

Do not force a full repository scan when the map can narrow the working set. Do not trust a stale map over source and tests.

## 3. Anti-debt engineering rules

Reject changes that make the next correct change materially harder without an explicit, time-bounded reason and owner.

- Keep each module/file cohesive around a responsibility, contract, or change axis.
- Split when responsibilities, owners, change frequencies, test seams, trust boundaries, or context needs diverge; do not split merely to meet a line count.
- Treat roughly 400-600 lines per source file or 50-80 logical lines per function as review triggers, not universal limits. Generated code and declarative data are exceptions when clearly marked.
- Avoid god objects, circular dependencies, hidden global state, duplicated business rules, action-at-a-distance, mixed UI/domain/infrastructure concerns, silent error swallowing, and compatibility behavior with no retirement owner.
- Prefer predictable names, explicit types/schemas, narrow public interfaces, dependency injection at real seams, and tests beside or clearly mapped to the behavior they protect.
- Refactor before adding a feature when the requested change cannot be isolated, tested, reviewed, or rolled back safely. Keep refactoring and behavior change separately reviewable when practical.
- Never create an abstraction without at least two credible consumers or a strong boundary/invariant reason. Never copy-paste a rule that should have one owner.

### Comment policy

Comments explain why the code exists, an invariant, a non-obvious trade-off, an external constraint, a security boundary, or a temporary workaround with owner/removal condition. Do not narrate obvious syntax or use comments to excuse confusing code. Public APIs and modules need concise contract documentation; complex algorithms need the assumptions needed to verify them. Update or remove stale comments in the same change.

### Concurrent-write isolation

Never let two agents edit one shared working tree. Read-only agents may inspect the same sources. Every write-capable child must use a separately provisioned, runtime-issued isolated worktree; its tools and working directory must be bound to that worktree, and its charter must declare the repository-relative paths it owns. The parent reserves workspace IDs and path scopes before activation. The lead is the single integration owner and merges accepted work serially after tests and conflict review.

An `isolated-worktree` string in JSON is only a validator-checked claim. Report write isolation as runtime-enforced only after the workspace was actually created and the child's environment was bound to it. If the runtime cannot provide isolation, keep children read-only and perform writes serially in the lead.

## 4. Artifact economy and single-source rules

Organization artifacts exist to reduce uncertainty, not to demonstrate activity. The control plane assigns each child `artifact_budget_units` from 1-8. One unit means one concise artifact or one bounded contribution to an existing canonical artifact; it is a relative output limit, not a word or token promise.

- Default to one project map/index plus the smallest set of lifecycle artifacts that have different owners, audiences, approval paths, or update cadences.
- Give every invariant, decision, interface, risk, error taxonomy, owner, and status one normative home. Other documents link to its stable heading or identifier and add only local consequences.
- Do not create separate summary, architecture, decision, runbook, and assurance files when bounded sections in fewer canonical artifacts remain navigable.
- A child proposes another artifact only when an existing canonical destination would mix responsibilities or make independent approval/history unsafe.
- Put the current verdict, version, owner, and blocking status at the top. Preserve append-only review history below it or behind a linked history section so stale BLOCK/PASS text cannot be mistaken for current state.
- During integration, consolidate duplicates before accepting more prose. Preserve evidence and dissent while removing repeated restatements.
- Replan or stop output when artifact growth exceeds the assigned budget without a new justified consumer or control boundary.

Artifact budgets never justify omitting required evidence, security controls, or human gates. They force links and prioritization before new files.

## 5. Context Capsule for every activated agent

Every child and descendant owns a bounded Context Capsule. The charter assigns `context_budget_units`, `artifact_budget_units`, `context_sources`, and `learning_authority`; the child may narrow its working set but may not silently broaden permissions, output scope, or memory scope.

The capsule contains:

```text
Mission and acceptance criteria:
Relevant project-map nodes:
Authoritative source paths and evidence:
Interfaces, invariants, and compatibility constraints:
Current facts, assumptions, decisions, and confidence:
Permissions, context/token envelope, and stop conditions:
Open questions and escalation triggers:
```

Context budget units are relative attention limits, not exact model tokens. The agent should keep only task-relevant material active, use pointers instead of copying large sources, and return distilled evidence rather than raw logs or full conversation history.

### Context lifecycle

- **Orient:** load the capsule and verify its paths and assumptions.
- **Work:** maintain an evidence ledger plus short assumption and decision lists.
- **Checkpoint:** after a milestone or before risky changes, record current result, changed artifacts, tests, unresolved risks, and next action.
- **Rebase/compact:** when context becomes broad, stale, repetitive, or contradictory, preserve canonical decisions/evidence, discard replaceable noise, reread the project map and current sources, and produce a fresh checkpoint.
- **Handoff:** return outcome, changed files/artifacts, interface effects, tests, decisions, unresolved risks, and the smallest sufficient next context.

Raw transcript dumping is not a handoff. A compact summary is not evidence unless it points to a source, test, or recorded decision.

## 6. Three-layer organizational memory plus studio state

Keep memory bounded and separate by purpose:

- **Episodic/task memory:** checkpoints and evidence for the current mission; archive or discard after closeout.
- **Semantic/project memory:** durable facts such as architecture, interfaces, incident lessons, ownership, and runbooks; write to versioned project artifacts.
- **Procedural/skill memory:** reusable methods, routing rules, validators, or scripts; promote only after cross-task evidence and governed Skill change.

Above project memory, **Studio State** persists portfolio items, finite investment horizons, Product Assets, durable responsibility seats, reality evidence, operating scorecards, and capability calibration across projects. Keep it in `STUDIO_STATE.json` using `studio-kernel.md`; link to project artifacts rather than copying them. Studio State may route work but cannot silently promote a local lesson into Skill policy.

Never use an agent's private recollection as the canonical project state.

## 7. Governed learning and self-improvement

An agent that discovers a defect pattern, useful method, review heuristic, or repeated source of rework creates a Learning Candidate:

```text
Observation and affected lifecycle stage:
Evidence and reproduction:
Proposed reusable rule, map update, test, runbook, or skill change:
Expected benefit and cost:
Applicability boundary and counterexamples:
Security/permission impact:
Independent evaluator:
Expiry or revalidation trigger:
```

Default child `learning_authority` is `propose`. A proposal becomes institutional memory only after:

1. evidence is reproducible or supported by multiple tasks/incidents;
2. an independent reviewer tries to falsify its generality and checks harmful edge cases;
3. the change is sandboxed or replayed when it affects workflow, prompts, code, evaluation, or routing;
4. the required decision owner approves it;
5. it is written to the narrowest authoritative destination and versioned;
6. its effect is measured and it can be reverted or retired.

Use `commit-approved` only for a designated state owner with `memory:write-approved` permission. No agent may approve its own learning, change its own evaluator or authority, rewrite failed history, or promote a local trick directly into the constitution. Constitution and root authority changes remain human-gated. Revalidate or retire stale rules so memory does not grow without bound.

## 8. Engineering gates in the lifecycle

Before integration, verify:

- project-map and nearest instruction changes are included when navigation or ownership changed;
- new code is cohesive, testable, and no harder to understand than the behavior requires;
- comments and API docs explain contracts and non-obvious reasons, not syntax;
- added dependencies and reused code have provenance, license, security, and maintenance evidence;
- context handoff identifies sources, tests, interface effects, and unresolved risk;
- artifacts stay within their machine-assigned budget, identify one normative home per fact, and show current status before history;
- any claimed learning is either an unapproved candidate or a traceable approved memory change;
- studio-scoped changes update the affected portfolio item, Product Asset, evidence freshness, responsibility handoff, and next event-driven review trigger before the mission cell dissolves;
- debt accepted for urgency has an owner, rationale, expiry/removal trigger, and compensating test or control.
- final compression preserves or links one Operating Control Packet per affected live Product Asset: durable/on-call owner, reconciliation control for money, support surface, SLIs/alerts, incident/safe state, maintenance envelope, retirement condition, and next reality-evidence trigger.
- independent findings and affected operating controls are represented in a manifest-bound valid `integration-v2` packet with recomputed evidence/attestation hashes, minimum high-risk applicability, and exact action-scoped authority; final prose uses or links the canonical validator-rendered decision, and no subject advances while the validator reports blockers.
