# Operating contracts

Use these compact formats. Omit fields that are genuinely irrelevant, but never omit permissions, acceptance criteria, budget, or stop conditions from an Agent Charter.

## Contents

1. Founder Conversation Packet and Founder Charter
2. Studio State and Portfolio Decision
3. Intent Brief
4. Organization Plan
5. Capacity input
6. Agent Charter
7. Task Contract
8. Decision Packet
9. Change Packet
10. Lossless assurance integration
11. Integration, telemetry, and closeout

## 1. Founder Conversation Packet and Founder Charter

Use for a new product, material feature, ambiguous strategic change, or human request to discuss/design before building. The conversation packet is a temporary view; the versioned Founder Charter is normative.

```text
Founder narrative in their language:
Current synthesis:
Observations and supplied evidence:
Human preferences/vision:
Inferences and assumptions:
Decided and undecided:
Material contradictions:
Options, including no action where meaningful:
AI recommendation and confidence:
Material dissent:
Highest-leverage question(s):
Next reversible discovery action:
```

The Founder Charter must record ID/version/state, Founder, purpose, target and excluded users, problem/current alternatives/evidence, desired change, value proposition, product/design principles, examples/counterexamples, non-goals, constraints, assumptions/unknowns/confidence, options/recommendation/dissent, success and failure evidence, risk appetite, rollback/stop conditions, human-reserved decisions, delegated authority, reversible prototype/research plan, authorized execution scope, milestone gates, revisit triggers, and append-only decision/evidence links.

## 2. Studio State and Portfolio Decision

Use `STUDIO_STATE.json` and the schema/invariants in `studio-kernel.md` when an opportunity, Product Asset, investment, operating obligation, or capability must persist across tasks. Start from `assets/studio-state.template.json` when no state exists.

Record each portfolio decision compactly:

```text
Portfolio decision ID and studio state version:
Item and current lifecycle state:
Decision owner and durable responsibility seat:
Recommended action and next finite horizon:
Founder Charter status and human-reserved gates:
Reality evidence, freshness, confidence, and causal limitations:
Alternatives including discover, queue, pause, and retire:
Estimated envelope and measured cost separately:
Existing-user, maintenance, migration, incident, and retirement obligations:
Stop conditions and failure thresholds:
Chosen action, dissent, and rationale:
Next evidence action and event-driven review trigger:
State transition and append-only history reference:
```

Run the platform-native portfolio planner before capacity planning. Its score is an estimate and cannot bypass a hard gate.

## 3. Intent Brief

```text
Outcome:
Target user or beneficiary:
Non-goals:
Evidence supplied:
Assumptions:
Open choices:
Options and trade-offs:
Risk and external-effect boundary:
Human-reserved decisions:
Next reversible action:
```

## 4. Organization Plan

```text
Human root owner and design decisions:
Founder Charter ID/version/state and authorization scope:
Founder Partner and any bounded advisory cells:
Studio portfolio decision, selected investment horizon, and persistent Product Asset/owner seat:
Lead organization steward:
Mission workstreams:
Logical functional roles:
Assurance roles:
Roles activated as children:
Roles retained by lead:
Task dependency graph:
Machine-selected active-agent cap and rationale:
Machine-selected topology and organizational-value drivers:
Machine-selected token tier and allocation:
Predicted single-agent versus selected-plan token units:
Machine-selected maximum spawn depth:
Machine-derived budget envelope:
Human gates:
Integration owner:
```

## 5. Capacity input

Save JSON and pass it to the platform-native capacity planner described in `SKILL.md`:

```json
{
  "runtime_active_limit": 4,
  "runtime_active_agents": ["/root", "/root/project-lead"],
  "runtime_snapshot_source": "collaboration.list_agents",
  "company_policy_version": "company-v5",
  "decision_level": 2,
  "mandatory_human_gate": false,
  "founder_discovery_required": true,
  "founder_charter_status": "explored",
  "items": [
    {
      "id": "user-research",
      "complexity": 3,
      "risk": 1,
      "estimated_units": 3,
      "context_units": 2,
      "coupling": 1,
      "context_isolation": 2,
      "specialist_need": 1,
      "critical_path": 2,
      "requires_separation_of_duties": false,
      "lifecycle_stage": "discovery",
      "cognitive_mode": "reuse-first-research",
      "parallelizable": true,
      "independent": true
    },
    {
      "id": "architecture",
      "complexity": 4,
      "risk": 3,
      "estimated_units": 4,
      "context_units": 4,
      "parallelizable": true,
      "independent": true,
      "requires_independent_verification": true
    }
  ]
}
```

The machine obtains runtime limits, active-agent names, Founder state, and all work-item scores. Complexity and context units are 1-5, risk and coupling are 0-4, context isolation/specialist need/critical-path value are 0-4, decision level is D0-D5 as an integer, and estimated units are 1-8. Every Boolean must be a literal JSON Boolean; string or numeric substitutes are invalid. The planner derives active occupancy from the names, accepts only `collaboration.list_agents` as authoritative provenance, rejects a conflicting or non-integer `runtime_active_now`, and returns `direct`, `governed-serial`, `organized`, `founder-discovery`, or `human-gated`. It reports token estimates separately from normalized quality, latency, specialist, and control value. Never ask the human to supply these operational values.

When `founder_discovery_required` is true, `founder_charter_status` is `raw`, `framed`, `explored`, `decision-ready`, or `authorized`. Before `authorized`, capacity items may use only `control`, `discovery`, `design`, or `verify`, and `implementation_activation_allowed` is false. For tasks that do not require Founder discovery, status is `not-required`.

If the runtime cannot expose active names, supply `runtime_active_now` with source `unspecified` and conservatively limit new creation. Refresh the authoritative names immediately before each spawn.

## 6. Agent Charter

Use JSON when validating delegation:

```json
{
  "id": "architecture-lead",
  "parent_id": "organization-steward",
  "mission": "Produce and challenge the system architecture",
  "deliverables": ["architecture decision record", "risk map"],
  "success_criteria": ["covers all approved requirements", "records alternatives"],
  "company_policy_version": "company-v5",
  "lifecycle_stage": "design",
  "cognitive_mode": "architecture-first-principles",
  "context_budget_units": 4,
  "artifact_budget_units": 2,
  "context_sources": ["PROJECT_MAP.md#architecture", "src/contracts", "tests/architecture"],
  "learning_authority": "propose",
  "token_tier": "medium",
  "permissions": ["repo:read", "work:write"],
  "delegable_permissions": ["repo:read"],
  "budget": {
    "token_units": 30,
    "cash": 0,
    "compute_units": 1
  },
  "spawn_quota": 0,
  "current_depth": 1,
  "max_depth": 2,
  "ttl_minutes": 60,
  "auditor_id": "organization-steward",
  "auditor_independence": "parent-accountable",
  "write_scope_mode": "isolated-worktree",
  "write_scope": ["architecture", "docs/architecture"],
  "workspace_id": "worktree-architecture-lead-01",
  "stop_conditions": ["deliverables accepted", "scope changes", "budget exhausted"]
}
```

A parent charter uses the same fields plus its available `delegable_permissions`, total budget, quota, depth, and lease. Track resources already committed to other active children:

```json
{
  "runtime_snapshot_source": "collaboration.list_agents",
  "runtime_active_agents": ["organization-steward", "architecture-lead", "assurance-1"],
  "authorized_auditor_ids": ["organization-steward", "assurance-1"],
  "authorized_workspace_ids": ["worktree-architecture-lead-01"],
  "reserved_workspace_ids": [],
  "reserved_write_scopes": [],
  "reserved_budget": {"token_units": 20, "cash": 0, "compute_units": 1},
  "reserved_spawn_units": 0
}
```

Token units are relative machine-planning weights, not promises of exact model tokens. Use a runtime hard limit when one is exposed. Creating a child reserves one unit for the child itself plus its `spawn_quota`. The active-agent and authorized-auditor lists must come from the current authoritative runtime snapshot; a fictional name is invalid. A write child additionally requires a runtime-issued isolated worktree ID and repository-relative scope. Atomically reserve budget, spawn units, workspace ID, and scope after approval and release them when the child lease ends. The runtime must actually bind the child's tools and working directory to that worktree; validation of JSON is not a sandbox. Validate with the platform-native implementation:

The parent and child must carry the same non-empty `company_policy_version`. `lifecycle_stage` and `cognitive_mode` must use the allowed values in `references/cognitive-modes.md`. `context_budget_units` is a machine-selected relative attention limit from 1-8, `artifact_budget_units` is a machine-selected relative output limit from 1-8, and `context_sources` must be a non-empty scoped list. The child depth must fit both its own and its parent's maximum. `auditor_id` must be active and authorized; `auditor_independence` records whether the parent is accountable or a distinct assurance agent is independent. A read-only child uses `write_scope_mode: read-only`, `write_scope: []`, and `workspace_id: none`. Children normally receive `learning_authority: propose`; `commit-approved` additionally requires `memory:write-approved` permission and a separately approved Learning Candidate. These fields are machine-selected company controls, not human scheduling inputs.

```text
powershell -File scripts/validate_charter.ps1 -Parent parent.json -Child child.json
<python-executable> scripts/validate_charter.py --parent parent.json --child child.json
```

## 7. Task Contract

Send this task-local packet to a child:

```text
Mission:
Why this work exists:
Company policy version and inherited constitution:
Lifecycle stage and primary/counter cognitive mode:
Exact scope:
Out of scope:
Original evidence and source paths:
Relevant project-map nodes and nearest instructions:
Exact parent-Charter path, child-Charter path, and validator command:
Inputs and current state:
Interfaces, invariants, assumptions, and current decisions:
Studio item/asset IDs, durable owner seat, lifecycle state, reality-evidence duties, and update destination:
Required deliverable:
Acceptance criteria:
Tools and permissions:
Auditor identity/independence and authoritative runtime roster:
Write scope, runtime-issued workspace ID, and actual worktree binding:
Budget and lease:
Dependencies:
Downstream consumers:
Reporting format:
Evidence, provenance/reuse, and maintenance duties:
Context and artifact budgets, checkpoint/rebase triggers, canonical destination, and handoff format:
Learning authority and Learning Candidate destination:
Spawn authority or prohibition:
Stop and escalation conditions:
```

## 8. Decision Packet

```text
Decision ID and level:
Accountable owner:
Question:
Evidence:
Assumptions and confidence:
Options, including no action:
Expected value and cost:
Failure modes and dissent:
Affected systems and people:
Permission or budget change:
Reversibility and rollback:
Required approver and verifier:
Chosen action and rationale:
Revisit trigger and date:
```

## 9. Change Packet

Use for code, prompt, model, workflow, organization, permission, metric, or policy changes.

```text
Change ID and type:
Proposer:
Current behavior:
Proposed behavior:
Reason and evidence:
Affected agents, interfaces, users, and invariants:
Risk and decision level:
Sandbox/replay plan:
Acceptance and failure thresholds:
Independent verifier:
Approver:
Canary scope:
Rollback mechanism:
Monitoring window:
Result and organizational learning:
Project-map/navigation update:
Learning Candidate or approved memory record:
```

## 10. Lossless assurance integration

When review findings or live operating obligations exist, freeze an independent `assurance-v1` manifest from `assets/assurance-manifest.template.json`, persist its SHA-256 in a parent/Founder/assurance artifact outside the integrator's write scope, then create the canonical `integration-v2` packet from `assets/integration-packet.template.json` and follow `references/integration-gate.md`. Preserve every manifest finding, subject, accountable-owner principal, authority gate, applicability decision, authorized verifier, and evidence digest exactly. Evidence and attestation references are manifest-relative non-reparse files whose SHA-256 values are recomputed; attestations use `evidence-attestation-v1` and bind dates. Record control truth as verified, declared-unverified, proposed, missing-blocker, or independently approved not-applicable.

Run the native integration validator before final delivery. Record its decision ID, validity, advancement result by subject, open P0/P1 IDs, blocking control fields, unsatisfied authority gates, and packet path in closeout. A valid HOLD packet is decision-ready but not release-ready.

## 11. Integration, telemetry, and closeout

```text
Outcome:
Accepted artifacts:
Rejected or superseded artifacts:
Cross-workstream contradictions resolved:
Verification evidence:
Project-map/navigation and architecture-debt assessment:
Context handoffs accepted or rejected:
Learning Candidates proposed, approved, rejected, or expired:
Studio portfolio transition, Product Asset stewardship handoff, operating scorecard, and capability-registry updates:
Human changes incorporated:
Active children created/reused/stopped:
Actual organization versus planned organization:
Started/ended timestamps and elapsed wall-clock interval:
Actual runtime tokens and telemetry source (or unavailable):
Planned token tier/weights, clearly labeled estimates:
Predicted single-agent versus selected-plan token units and assumptions:
Quality, context-isolation, specialist, critical-path, and control drivers:
Child activations, reuse, coordination actions, and rework cycles:
Budget or coordination assessment:
Remaining risks:
Decisions to revisit:
Operating Control Packet for every affected live asset: durable/on-call owner, reconciliation control when money is affected, support surface, SLIs/alerts, incident/safe state, maintenance envelope, retirement condition, and next evidence trigger:
Evaluation runtime facts when organization feasibility is scored: frozen active limit, authoritative roster/occupancy, available slots, and actual activated topology:
Integration certificate: packet path, decision ID, validator/version, valid result, advancement by subject, open P0/P1, blocking controls, and unsatisfied gates:
```

Do not convert relative token units into fictional model-token counts. Actual tokens and exact latency are measurements only when the runtime exposes them. Word counts, artifact size, child count, coordination messages, and rework cycles are useful observable proxies but must be labeled as such.
