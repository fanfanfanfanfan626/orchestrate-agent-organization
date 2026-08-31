# AI company operating architecture

## Contents

1. First principles
2. Logical organization
3. Product-delivery lifecycle
4. Shared state and memory
5. Dynamic formation and dissolution
6. Organizational fitness

## 1. First principles

Build the organization to correct structural limits of isolated agents:

- **Bounded context:** one agent loses fidelity as goals, evidence, interfaces, and history accumulate. Decompose around stable artifacts and give each mission only the context it needs.
- **Stochastic execution:** fluent output is not evidence. Require acceptance criteria, tests, provenance, and independent falsification proportional to risk.
- **Local optimization:** individually good product, architecture, code, security, and operations decisions can conflict. Assign one integration owner and make interfaces explicit.
- **Weak continuity:** a product spans many turns and changes. Preserve decisions, constraints, artifacts, incidents, and measurements outside conversational memory.
- **Authority ambiguity:** recommendations, approvals, implementation, deployment, and audit are different powers. Name the accountable owner and enforce permission boundaries.
- **Change risk:** self-modification without impact analysis creates drift. Route prompt, model, workflow, evaluator, permission, and budget changes through governed change control.
- **No natural customer feedback loop:** completion is not product success. Carry observed outcomes, defects, usage, cost, and human feedback into the next planning cycle.
- **Task-local existence:** a successful project organization disappears at closeout unless portfolio, ownership, operating obligations, and evidence persist independently of its Agents. Use the Studio Kernel to preserve this continuity.

The goal is not to imitate headcount. The goal is to transform model capability into repeatable product delivery with continuity, accountability, professional standards, independent challenge, safe change, and learning.

## 2. Logical organization

Maintain these logical layers. Instantiate an agent only when workload, context isolation, specialist capability, latency, or separation of duties justifies one.

1. **Human Founder/Chair and Founder Office:** the human owns purpose, target users, value, experience preferences, material trade-offs, authorization, external commitments, and D4-D5 decisions. One Founder Partner helps the human form and maintain the Founder Charter; temporary advisers inform but never vote or authorize. Humans may enter any layer at any time.
2. **Studio Kernel and portfolio stewardship:** persists opportunities, investment horizons, Product Assets, reality evidence, capability calibration, durable responsibility seats, and continue/pause/retire decisions across tasks. It is state and event-driven logic, not a permanently running committee.
3. **Executive control plane:** receives authorized and portfolio-selected intent, owns the task graph, topology, permissions, machine budgets, replanning, and final accountability. It cannot convert an unapproved idea or unfunded horizon into material execution.
4. **Program and product layer:** converts intent into measurable outcomes, requirements, journeys, milestones, dependencies, release criteria, and operating scorecards. It keeps product decisions distinct from implementation choices.
5. **Mission cells:** cross-functional, temporary teams accountable for one end-to-end artifact or outcome. A cell may combine product, design, architecture, implementation, test, and operations work instead of handing fragments between simulated departments.
6. **Functional stewardship:** maintains reusable standards for product, design, architecture, engineering, security, data, quality, and operations. A steward reviews conformance; it does not take ownership away from the mission cell.
7. **Independent assurance and audit:** challenges claims, permissions, interfaces, evidence, safety, and release readiness. It must be able to reject material work and must not depend solely on the producer's evidence.
8. **Platform, state, and operations:** supplies tools, reusable components, artifact storage, decision history, evaluation, observability, incident response, and organizational telemetry.

Use a matrix only where both mission ownership and functional standards add value. Keep one accountable mission owner, one integration owner, and one independent assurance path. Do not create consensus committees for ordinary work.

## 3. Product-delivery lifecycle

Run an evidence-producing lifecycle:

```text
problem or opportunity intake
→ portfolio discovery / rejection / investment decision
→ founder narrative and framing where material product intent is unsettled
→ product/design exploration and challenge
→ explicit Founder Charter authorization
→ architecture and interface contracts
→ machine organization and execution
→ continuous integration
→ independent verification
→ staged release and rollback readiness
→ operations, incidents, and user evidence
→ portfolio continue / scale / pause / retire decision
→ learning and governed adaptation
```

At every transition define the artifact, owner, acceptance evidence, downstream consumer, open human choice, and rollback/revisit trigger. Stages may overlap when interfaces are stable; they must not disappear merely because an agent can generate the next artifact immediately.

Treat initial implementation as a minority of the product's economic life. Run the standing loop:

```text
observe → prioritize → reuse/impact research → change → integrate/test
→ release → operate → debug → maintain/evolve → deprecate/retire → observe
```

Every feature inherits existing compatibility, data, security, observability, support, and operational obligations. Every defect produces evidence, a regression oracle, a staged correction, and a learning item. Every replaced path gets a migration and retirement owner; otherwise “temporary” complexity becomes permanent maintenance cost.

For material work, require:

- a problem and target-user statement before solution optimization;
- explicit human authorization of a versioned Founder Charter before implementation intended for integration;
- product acceptance criteria before implementation decomposition;
- interface and failure invariants before parallel execution;
- producer tests plus independent challenge before release;
- staged rollout, observability, and rollback before external effect;
- post-release outcome evidence before declaring the product successful.
- explicit maintenance, debug, upgrade, support, and retirement ownership before closing the delivery cell.

## 4. Shared state and memory

Keep a centralized, append-only organizational ledger containing:

- Founder Charter versions, authorization state, intent, non-goals, human-reserved choices, and current mandate;
- studio portfolio items, finite investment horizons, Product Assets, durable owner seats, reality evidence, operating scorecards, and capability records;
- requirements, task graph, ownership, dependencies, and status;
- decisions, alternatives, dissent, assumptions, and revisit triggers;
- interface contracts, schemas, threat models, and failure invariants;
- charters, permissions, leases, machine budgets, and runtime topology;
- code/design artifacts, tests, evaluation evidence, and provenance;
- releases, rollbacks, incidents, SLOs, cost, user outcomes, and postmortems.

Children receive task-local projections of this ledger rather than the entire conversation. The lead reconciles returned artifacts into the canonical state. Never treat chat history or agent consensus as the source of truth.

## 5. Dynamic formation and dissolution

Form a mission cell only after the Studio Kernel permits the relevant discovery, funded, operating, or retirement horizon and the capacity planner identifies positive organizational value from one or more of:

- narrower context materially improves reasoning fidelity;
- a specialist tool or standard is needed;
- independent work shortens a critical path;
- an interface has a clear owner and acceptance contract;
- separation of duties or adversarial assurance is required;
- focused execution is expected to reduce total tokens or rework.

Do not form a cell when coupling, duplicated context, unclear acceptance criteria, or integration cost dominates those gains. Permit a cell to propose descendants, but activate them only through the same planner, permission, lease, and global-capacity rules.

Dissolve or reuse a cell when its artifact is accepted, its interface changes, its marginal value drops, or another cell makes it redundant. Persistent functions should normally be standards and state, not permanently running agents.

## 6. Organizational fitness

Optimize a multi-objective score, not headcount or tokens alone:

- product outcome and human acceptance;
- correctness, coverage, coherence, and maintainability;
- risk, security, privacy, reversibility, and auditability;
- cycle time and critical-path latency;
- expected total tokens, context duplication, coordination, and rework;
- reuse of decisions, standards, components, and evidence;
- calibration between predicted and observed results.

Record actual model tokens when exposed, but never make token minimization override mandatory human authority, safety, independent assurance, or product correctness. Use post-task evidence to recalibrate the planner through a governed Change Packet; do not let the planner silently rewrite its own objectives.
