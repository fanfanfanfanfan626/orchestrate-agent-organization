# Studio Kernel: persistent portfolio and product stewardship

Use this reference when work crosses projects or invocations: selecting opportunities, allocating investment, operating released products, reviewing reality evidence, transferring stewardship, pausing work, retiring assets, or calibrating organizational capability.

The Studio Kernel is persistent state plus event-driven decisions. It is not a set of permanent Agent instances, a simulated board, or a background process the runtime cannot actually provide.

## Contents

1. First principles and authority
2. Canonical studio state
3. Portfolio state machine
4. Durable product stewardship
5. Reality evidence and scorecards
6. Portfolio planning and economics
7. Capability registry
8. Event-driven operation
9. Transition gates and failure controls

## 1. First principles and authority

The Kernel exists because a task-local conversation cannot preserve responsibility, compare investments, observe a released product, or learn across projects by itself.

Apply four separations:

- **Value authority:** the human Founder defines purpose, forbidden outcomes, risk appetite, strategic boundaries, and reserved decisions.
- **Organization authority:** the AI control plane selects investigations, task graphs, temporary Agents, internal allocation, and reversible actions inside the mandate.
- **Enforcement authority:** the runtime controls tools, identity, permissions, leases, workspaces, schedules, and external effects.
- **Epistemic constraint:** reality evidence updates confidence and triggers review; evidence informs an accountable decision owner but does not define human values or decide by itself.

Optimize expected durable value, not output volume, Agent count, or project completion. Stopping a weak investment is a successful control outcome. Existing users, safety obligations, and retirement costs cannot be ignored merely because a new opportunity scores higher.

Persistent objects are records, responsibility seats, evidence, and assets. Agent instances remain leased and replaceable. Never keep an Agent alive only to imitate a permanent employee.

## 2. Canonical studio state

Use one machine-readable `STUDIO_STATE.json` as the normative state and an optional concise `STUDIO_MAP.md` as human navigation. The map links to state objects and product/project artifacts; it does not duplicate them.

The state contains five object classes:

1. **Portfolio items:** opportunities, investigations, investments, builds, operating products, paused work, and retired bets.
2. **Product assets:** released systems or durable outputs with stewardship, feedback, operations, recovery, maintenance, and retirement obligations.
3. **Investment envelope:** available and reserved investment, human-attention, maintenance, and risk-capacity units. Units are relative planning weights unless the runtime supplies measured cost.
4. **Reality evidence:** dated, sourced observations of user outcome, adoption, reliability, cost, maintenance load, harm, and external constraints.
5. **Capability records:** cross-project evidence about what the studio can and cannot do reliably.

Each portfolio item has one normative record containing:

```text
id, title, current_state, previous_state, state_changed_at:
Founder Charter reference and status:
human-reserved decisions and mandatory gate:
problem, target user, desired outcome, non-goals:
strategic alignment and evidence confidence:
estimated investment, human attention, maintenance, and risk units:
reality evidence references and freshness:
success evidence and failure signals:
stop conditions and whether one is triggered:
next evidence action and review triggers:
accountable durable seat and current custody lease:
linked product asset, if any:
decision history and dissent references:
```

Do not store secrets, raw user data, full transcripts, or duplicated project documentation in studio state. Link to authoritative sources.

## 3. Portfolio state machine

Use this lifecycle:

```text
opportunity → discovery → funded → build → operate → scale
      │            │         │        │         │
      └────────────┴─────────┴────────┴─────────┤
                                                ↓
                                    pause ↔ resume
                                                ↓
                                             retire
```

Meaning:

- `opportunity`: a problem or possibility exists; no investment commitment.
- `discovery`: bounded reversible evidence gathering is authorized.
- `funded`: the studio reserves resources for an explicitly defined next investment horizon.
- `build`: implementation intended for integration is active.
- `operate`: a released asset is under ongoing stewardship and reality observation.
- `scale`: fresh outcome evidence justifies broader investment or exposure.
- `pause`: work or growth stops safely while responsibility and evidence remain.
- `retire`: external effects are removed or transferred, obligations are closed, and history is retained.

Every investment horizon is finite. `funded` never means “finish regardless of evidence.” It authorizes only the next milestone, budget envelope, and stop conditions.

Apply one legal state transition at a time and persist it before planning the next transition. Founder authorization does not allow `opportunity` to skip `discovery`; after the bounded discovery record is persisted, a later planner invocation may compare `discovery → funded` against the portfolio envelope.

Allowed default transitions:

- `opportunity → discovery | pause | retire`
- `discovery → funded | pause | retire`
- `funded → build | discovery | pause | retire`
- `build → operate | discovery | pause | retire`
- `operate → scale | pause | retire`
- `scale → operate | pause | retire`
- `pause → discovery | funded | build | operate | retire`, but only by restoring the gates required by the target state
- `retire` is terminal unless the human explicitly creates a new linked opportunity; do not silently resurrect it.

## 4. Durable product stewardship

Every `operate`, `scale`, or externally consequential `pause` item links to a Product Asset record. The record persists when a mission cell dissolves.

Required stewardship fields:

```text
asset_id and lifecycle state:
durable owner seat:
current custodian Agent and custody lease, or unassigned event-driven custody:
user feedback channel:
observability/evidence source:
incident and escalation route:
runbook and rollback/safe-state reference:
maintenance envelope and dependency obligations:
known risks and compatibility commitments:
retirement conditions and procedure:
evidence freshness limit and next review triggers:
```

The owner seat is a stable responsibility identifier, not proof that an Agent is continuously active. When a trigger fires, the control plane assigns a leased custodian and supplies a Context Capsule. Custody ends or transfers with a distilled handoff; responsibility does not disappear.

Do not release a product whose feedback, observability, incident route, safe state, maintenance envelope, or durable owner seat is missing. Do not pause an external product by abandoning it; record safe-state and remaining obligations.

## 5. Reality evidence and scorecards

Rank evidence by proximity to the claimed outcome:

1. observed user or external outcome;
2. production reliability, cost, incident, and behavior data;
3. controlled experiment, replay, or representative simulation;
4. executable tests and artifact inspection;
5. source-backed analysis;
6. Agent explanation or consensus.

Lower levels can justify discovery or testing, not claims of market success. Multiple Agents sharing data, model family, prompt assumptions, or evaluation criteria are not epistemically independent merely because their names differ.

Each evidence record states source, observed time, freshness limit, affected claim, baseline, current value, target or failure threshold, confidence, causal limitations, and whether the producer controls the source.

The operating scorecard covers only decision-relevant measures:

- desired user or beneficiary outcome;
- adoption or continued use when applicable;
- reliability, incidents, safety, privacy, and negative externalities;
- measured or bounded operating cost;
- human-attention and support burden;
- maintenance load, dependency health, and architecture debt;
- prediction-versus-actual error;
- evidence freshness and missing observations.

Never optimize a proxy after it diverges from the Founder Charter's purpose. A metric change is a governed decision, not a way to hide underperformance.

## 6. Portfolio planning and economics

Run `scripts/plan_portfolio.ps1` on Windows or `scripts/plan_portfolio.py` elsewhere before creating an execution organization for a studio-scoped item. The planner validates state invariants, applies hard gates, ranks eligible investments, and returns a recommendation such as `discover`, `fund`, `continue`, `revalidate`, `pause`, `retire`, `human-gated`, or `retain-retired`.

Use the planner as a bounded decision aid:

- hard gates and existing obligations override relative scores;
- protect maintenance, incident, migration, and retirement obligations before optional new work;
- scale only with fresh reality evidence and a valid Product Asset record;
- reject or pause work with a triggered stop condition;
- prefer a reversible evidence action when uncertainty is the main problem;
- compare marginal investment horizons, not entire imagined product lifetimes;
- reserve human attention as a scarce resource;
- report estimates separately from measured cost and outcome.

The planner's score is a transparent heuristic, not ROI, truth, or an authorization token. The accountable owner records the chosen action, evidence, dissent, and revisit trigger. D3-D5, external spend, sensitive permissions, root policy, and human-reserved decisions keep their existing gates.

## 7. Capability registry

Capability records describe calibrated organizational performance, not self-esteem. Record domain, task class, evidence count, successes, failures, prediction error, effective controls, known limitations, last validation, and evidence references.

Use these statuses:

- `candidate`: observed in one task or not independently challenged;
- `validated`: supported by at least two materially distinct tasks plus independent review;
- `degraded`: new evidence shows lower reliability or stale assumptions;
- `retired`: no longer relied upon.

A capability record may influence routing only inside its evidence boundary. One success cannot promote a method to `validated`. Constitution, permission, evaluator, or human-gate changes remain governed separately and cannot be inferred from capability performance.

## 8. Event-driven operation

Review studio state only when an event can change a decision:

- the human adds or changes an opportunity, value, boundary, or priority;
- discovery produces material evidence;
- an investment milestone is reached or missed;
- a stop, failure, risk, cost, or human-attention threshold fires;
- an incident or external constraint changes obligations;
- operating evidence becomes stale or contradicts the expected outcome;
- an owner/custodian lease ends or a responsibility gap appears;
- a product requests scale, pause, migration, or retirement;
- a cross-project capability claim gains falsifying or confirming evidence.

Do not simulate weekly portfolio meetings or keep idle Agents polling. If the runtime supports schedules or monitors, configure them only for explicit evidence and expiry triggers. Otherwise record the next trigger and evaluate it at the next relevant invocation.

## 9. Transition gates and failure controls

- `discovery` requires a real problem/beneficiary hypothesis, a bounded evidence action, owner seat, stop conditions, and review trigger.
- `funded` requires a decision-ready investment horizon, available envelope, success/failure evidence, and no unresolved mandatory gate.
- `build` requires an explicitly `authorized` Founder Charter.
- `operate` requires accepted release evidence and a complete Product Asset record.
- `scale` requires fresh externally grounded outcome evidence, acceptable risk/cost/maintenance, and no triggered stop condition.
- `pause` requires a safe-state, remaining-obligation owner, resume/retire trigger, and user/external communication plan when applicable.
- `retire` requires an exit/migration record, external-effect removal or transfer, retained evidence, and closure of remaining obligations.

Failure controls:

- no portfolio score may bypass a hard gate;
- every recommended next state must be allowed from the current state, and the persisted recommendation must validate as the next invocation's input;
- no project remains active merely because work already started;
- no new opportunity may starve live-product safety or retirement obligations;
- no Agent can validate its own capability promotion;
- no stale or producer-only evidence may justify scale;
- no missing owner is repaired by inventing a permanently running Agent;
- no unobserved product may be declared successful;
- no retired project is silently resurrected;
- no planner estimate is reported as measured economics;
- no studio state claim is called runtime-enforced without an actual persistent store, identity source, and external evidence binding.
