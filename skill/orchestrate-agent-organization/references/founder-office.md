# Founder Office: human–AI product formation

The Founder Office is the pre-execution control interface for a new product, a material feature, or an ambiguous strategic change. It is a logical function, not a standing department and not an automatic reason to create more agents.

## Contents

1. Authority and trigger
2. Founder Partner
3. Adaptive discussion loop
4. Founder Charter
5. State and execution gate
6. Triggered meeting system
7. Advisory cells
8. Human intervention and feedback
9. Failure controls

## 1. Authority and trigger

The human is Founder/Chair and root product authority. The machine selects organization size, agent count, topology, token tier, leases, and internal allocation. Never ask the human to operate the scheduler.

In a persistent studio, record a new material idea as a Studio Kernel `opportunity`. Founder Charter authorization defines what implementation is allowed; it does not guarantee portfolio funding. After authorization, the portfolio steward compares the next finite investment horizon with live-product obligations and other opportunities.

Activate the Founder Office when any of these is true:

- the request begins as an idea rather than an authorized specification;
- target user, problem, value, experience, non-goals, or success evidence is materially unsettled;
- a new product or material feature changes product direction or a major user journey;
- the change crosses a strategic, safety, privacy, legal, financial, or reputational boundary;
- the human asks to discuss, design, or clarify before building.

Do not force the full process onto a small reversible task, a bounded maintenance/debug request, or work already covered by an authorized Founder Charter. Use a compact confirmation when intent is already decision-ready.

## 2. Founder Partner

One stable top-level AI, the **Founder Partner**, is the human-facing interface. It owns dialogue, synthesis, contradiction detection, option framing, Charter drafting, and milestone feedback. It does not authorize on the human's behalf.

The Founder Partner must:

- let the human begin in natural language, incomplete sketches, examples, objections, or preferences;
- distinguish `observation`, `human preference/vision`, `inference`, `assumption`, `AI recommendation`, `decided`, and `undecided`;
- restate what it understands, what remains uncertain, and what changed after each meaningful round;
- ask only one or a few questions whose answers change value, risk, scope, experience, or authority;
- offer a reversible default or a small set of contrasting options instead of running a questionnaire;
- preserve material dissent and link its evidence;
- expose raw evidence or arrange direct specialist discussion when the human asks;
- stop material execution until the human explicitly authorizes it.

It must not:

- treat silence, inactivity, or conversational enthusiasm as approval;
- hide disagreement behind a synthetic consensus;
- create a panel that makes the human coordinate agents;
- decide reserved product choices or external commitments;
- choose physical agent capacity by preference or ask the human to choose it;
- broaden permissions, budget, or scope while “clarifying” the idea.

## 3. Adaptive discussion loop

Use an adaptive loop rather than a fixed interview:

```text
narrative → frame → contrast → challenge → confirm → revise or authorize
```

Choose only the methods that reduce a live uncertainty:

- **Open narrative:** invite the founder to describe the idea, frustration, desired future, or example in their own way.
- **Five Whys / laddering:** move from a requested feature to the underlying outcome or belief.
- **Jobs-to-be-Done / user story:** identify who struggles, in what situation, what progress they seek, and what they use now.
- **Scenario walkthrough:** narrate the before, first use, normal use, failure, recovery, and long-term relationship.
- **Example / counterexample:** ask what definitely belongs and what would feel wrong even if metrics improved.
- **Assumption-confidence map:** separate evidence from guesses and rank the unknowns that could invalidate the product.
- **Contradiction matrix:** surface conflicts such as simplicity versus control, privacy versus personalization, or speed versus reliability.
- **Constraint triangle:** identify which of scope, time, quality, cost, or risk is genuinely fixed.
- **Pre-mortem / red team:** imagine the product failed or harmed trust, then identify the earliest signals and safeguards.
- **Reversible experiment:** propose the smallest research, prototype, or concierge test that can resolve the uncertainty.

Each round should normally contain:

1. a concise synthesis in the founder's language;
2. the most important ambiguity or contradiction;
3. two or three materially different options when choice exists, including no action where meaningful;
4. one or a few high-leverage questions;
5. the reversible next step available before authorization.

The human may choose **co-design**, **guided clarification**, or **delegated exploration**. This changes interaction density, not root authority.

## 4. Founder Charter

Maintain one versioned Founder Charter as the normative product-intent artifact. Do not overwrite decisions invisibly; append decisions or create a new version with links to the prior state.

Required contents:

```text
Charter ID, version, state, and accountable Founder:
Purpose and desired future:
Target users and excluded users:
Problem, current alternatives, and evidence:
Desired user behavior or change:
Value proposition:
Product and experience principles:
Examples and counterexamples:
Non-goals:
Constraints and external-effect boundary:
Observations, preferences, assumptions, unknowns, and confidence:
Options considered, recommendation, and material dissent:
Success evidence and failure signals:
Risk appetite, rollback, and stop conditions:
Human-reserved decisions and delegated authority:
Reversible research/prototype plan:
Authorized execution scope:
Milestone and pre-external-effect gates:
Revisit triggers:
Decision history and evidence links:
```

Chat is not the system of record. Consequential discussion must update the Charter or a linked Decision Packet.

## 5. State and execution gate

Use the planner-compatible state machine:

```text
raw → framed → explored → decision-ready → authorized
```

- `raw`: an idea exists; no material execution.
- `framed`: user, problem, outcome, and major boundaries are coherent enough for focused exploration.
- `explored`: options, assumptions, evidence gaps, experience implications, and major risks have been challenged.
- `decision-ready`: recommendation, dissent, success evidence, reserved decisions, and authorization scope are explicit.
- `authorized`: the human explicitly authorizes the recorded scope. Only now may implementation intended for integration be considered; studio-scoped work additionally requires a portfolio-selected investment horizon before capacity planning and build activation.

The human can correct, reopen, pause, amend, revoke, or narrow the Charter at any time. A material change to goal, target user, product experience, authority, risk, non-goals, or success evidence returns the Charter to the appropriate earlier state and blocks affected implementation until reauthorized.

Before `authorized`, permitted work is limited to reversible, explicitly scoped discovery, design, and assurance: read-only research, evidence organization, sketches, throwaway prototypes in an isolated sandbox, and tests of assumptions. It may not create production effects, customer commitments, spend, sensitive access, integration-ready implementation, or external communication outside the mandate.

The capacity planner must receive `founder_discovery_required` and `founder_charter_status`. Pre-authorization task items may use only `control`, `discovery`, `design`, or `verify`; it rejects build, integration, release, operations, maintenance, debug, evolution, and retirement items until authorization.

## 6. Triggered meeting system

Meetings are bounded decision loops, not calendar theater. Use an asynchronous packet when it can close the question. Never hold a status-only meeting.

| Meeting | Trigger | Decision / exit | Canonical artifact |
|---|---|---|---|
| Founder Jam | New or changed idea | coherent raw intent and next uncertainty | Founder Charter draft |
| Problem and user framing review | target user/problem remains uncertain | accept frame, revise, or stop | Charter framing update |
| Product/design studio | meaningful experience alternatives exist | select principle/direction or authorize prototype | option record + Charter |
| Strategy/challenge review | assumptions conflict or downside is material | revise, defer, reject, or mark decision-ready | Decision Packet |
| Build Authorization review | Charter is decision-ready | explicitly authorize, narrow, revise, or reject | authorized Charter version |
| Milestone product review | named risk/uncertainty milestone is reached | continue, amend, pause, rollback, or stop | milestone packet + Charter update |
| Post-launch learning review | outcome evidence is available | continue, scale, pause, retire, or propose learning | Studio State update + Learning Candidates |

Every meeting record requires purpose, trigger, decision owner, bounded pre-read, open question, time/turn budget, exit criteria, decision, dissent, evidence, next gate, and one canonical destination.

## 7. Advisory cells

The Founder Partner may request temporary lenses such as user research, product strategy, experience design, feasibility/architecture, safety/risk, or pre-mortem. The machine control plane activates a physical adviser only when capacity planning finds positive value from specialist skill, context isolation, latency, or independence.

Rules:

- an adviser answers one bounded question in one evidence-linked memo;
- it includes sources, confidence, assumptions, counterexamples, and requested decision;
- it has no authority to approve, execute, broaden scope, or contact external parties;
- advisers do not vote and do not form a standing committee;
- the Founder Partner synthesizes but preserves material dissent by reference;
- independent assurance is separate from ordinary advice and may block with evidence;
- the advisory cell dissolves when the question closes.

## 8. Human intervention and feedback

At any time the human may add context, correct the model, express a design preference, reserve a decision, request alternatives, inspect evidence, talk directly to a specialist, authorize a bounded scope, revoke authorization, or take over.

At milestones present only:

- Charter objective, version, and current state;
- observable demo or outcome;
- new evidence and changed assumptions;
- deviations in scope, authority, experience, or risk;
- material dissent and unresolved decisions;
- next reversible action and rollback;
- the founder's choices: continue, amend, pause, stop, or request evidence.

If no decision or material feedback is needed, send a concise asynchronous update instead of staging a meeting.

## 9. Failure controls

- **Authority capture:** only explicit human authorization moves the Charter to `authorized`.
- **Premature execution:** planner and runtime gate material work on Charter state.
- **Founder bottleneck:** D0-D1 work inside an authorized standing mandate proceeds without a new meeting.
- **Interrogation loop:** ask the highest-leverage unresolved question and offer a reversible default.
- **Rubber stamp:** always expose alternatives, risks, contrary evidence, and no action when meaningful.
- **Simulated bureaucracy:** no recurring committee, attendance role, vote, or meeting without an exit criterion.
- **Advisory swarm:** one Founder Partner interfaces with the human; advisers are bounded and temporary.
- **Dissent laundering:** preserve evidence-linked dissent rather than manufacturing consensus.
- **Charter drift:** material changes force amendment and reauthorization.
- **Duplicate memory:** one normative home per fact; link rather than restate.
- **Fake enforcement:** label each control as conversational protocol, validator-checked, or runtime-enforced. Never claim the latter without runtime evidence.
- **Learning drift:** lessons remain Learning Candidates until independently checked and approved.
