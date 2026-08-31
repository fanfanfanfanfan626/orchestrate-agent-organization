# Lossless assurance integration gate

Use this gate whenever independent review produces findings, a material incident/change reaches final synthesis, or an affected live product/investment has operating obligations. The typed packet is normative; prose is a view generated from or linked to it.

## Contents

1. First principle
2. Canonical packet
3. Review-obligation rules
4. Operating-control truth states
5. Authority gates
6. Validation and delivery

## 1. First principle

Review capability has no organizational value if the integrator can omit, soften, or falsely close its findings. Preserve assurance findings as typed obligations before compression. A safe `HOLD` decision may be delivered with open blockers; an advancement decision may not.

Do not use role count, consensus, path-shaped names, planned controls, or generated tests as evidence that a control exists or works.

## 2. Canonical packet

First have independent assurance freeze `assurance-v1` from `assets/assurance-manifest.template.json`. It is the source of the complete finding set, affected subjects, canonical accountable-owner principal, normative safe action, allowed non-applicable controls, exact authority action/scope/version, authorized verifiers, and typed evidence catalog. Record its SHA-256 out of band in a validated parent Charter or Founder/assurance decision that the producer and final integrator cannot write. Do not let the final integrator derive these fields or derive the trusted digest from the manifest it is validating.

Then start `integration-v2` from `assets/integration-packet.template.json`. Give every packet:

- a stable decision ID plus the exact manifest ID and raw-file SHA-256, which must also match the externally supplied trust anchor;
- the exact complete review finding and affected-subject sets;
- exactly one obligation for every finding;
- one Operating Control Packet for every affected Product Asset, external paused product, or live investment that still carries financial, customer, operational, maintenance, or retirement risk;
- every human, machine, or external authority gate referenced by an obligation or resume path.

Keep this JSON beside the canonical decision/change artifact. The final human-facing output must derive from it or link to it; prose cannot override its status.

## 3. Review-obligation rules

Each manifest finding records a stable ID, `P0|P1|P2`, subject, statement, exact `required_action`, evidence keys, and required gate IDs. Its obligation repeats them exactly.

Allowed obligation states:

- `open-blocker`: accepted and unresolved; record owner, required evidence, and the manifest's safe action. The validator generates the final delivery view.
- `contested-blocker`: challenged with cited evidence but still blocking until resolved.
- `verified-closed`: required evidence exists and a named verifier has closed it. P0/P1 verification must be independent of the owner.

Never delete a finding because it was inconvenient, delete both sides of the mapping, compress its requirement, or mark it closed from producer text. The validator requires exact manifest-set equality.

A `verified-closed` obligation must cover every required evidence key using passing, fresh records from the manifest catalog. Its owner principal must exactly equal the subject owner frozen in the trusted manifest; P0/P1 verifier independence compares those canonical principals, not a producer alias. The record binds artifact and attestation digests, scope, decision version, and a verifier from the manifest's authorized roster. Both references must be relative files inside the manifest directory and may not traverse symlinks, junctions, or other reparse points; the validators recompute their SHA-256 values. The attestation is JSON with schema `evidence-attestation-v1` and exactly binds evidence ID, decision ID, subject, evidence key, scope, decision version, result, verifier, observation date, and freshness date.

## 4. Operating-control truth states

For each subject, type all nine controls:

`durable_owner`, `on_call`, `reconciliation`, `support_surface`, `slis_alerts`, `incident_safe_state`, `maintenance`, `retirement`, `next_evidence_trigger`.

Use only:

- `verified`: cited evidence shows the control exists and was checked.
- `declared-unverified`: a source claims it exists, but it has not been checked.
- `proposed`: the control is planned, not present.
- `missing-blocker`: it is absent and blocks advancement.
- `not-applicable`: independent assurance allowed that exact field for the subject. The integrator cannot declare applicability.

Every verified field references passing typed manifest evidence for `control:<field>`. Its rationale is the canonical `Verified by manifest evidence: <ordered evidence IDs>` string, so stale negative prose cannot coexist with a verified state. A filesystem-looking runbook/channel/dashboard name or arbitrary evidence string is not evidence.

For high/critical-risk advancement, durable ownership, on-call, SLIs/alerts, incident safe state, maintenance, retirement, and the next evidence trigger are never non-applicable. Product Assets and external paused products also require a support surface; money-bearing subjects require reconciliation. Independent assurance may narrow applicability elsewhere, but cannot waive this minimum matrix.

Safe actions are `hold`, `pause`, `discovery`, `revalidate`, `operate-safe`, `human-gated`, `retire-review`, or `retire`. `resume`, `release`, `scale`, and `cutover` are advancement actions. An advancement action is invalid while its subject has:

- any open or contested P0/P1;
- any declared-unverified, proposed, or missing control;
- any required authority gate that is not satisfied.

For high/critical-risk advancement, every applicable control must be `verified`.

## 5. Authority gates

Record gate ID, subject, exact action, scope, authority (`human|machine|external`), decision version, status, evidence, and rationale. These values come from the independent manifest. A subject with manifest gates may advance only through a gate for that exact action; a `resume` approval cannot authorize `scale` or `cutover`. A satisfied gate uses the same canonical evidence rationale as a verified control.

When policy or the Founder reserves recovery, release, scale, cutover, pricing, money, legal exposure, or broad external effect, the subject must reference that gate. A required future recovery gate may coexist with a valid safe pause; it still makes advancement false.

## 6. Validation and delivery

Run the native validator after findings are imported, after integration changes, and immediately before final delivery:

```text
powershell -File scripts/validate_integration.ps1 integration-packet.json assurance-manifest.json <trusted-manifest-sha256>
<python-executable> scripts/validate_integration.py integration-packet.json assurance-manifest.json <trusted-manifest-sha256>
```

Interpret results precisely:

- `valid=false` / exit 2: reject the synthesis; repair missing, softened, contradictory, or falsely closed records.
- `valid=true` with `advancement_allowed_by_subject=false`: deliver the validator-generated canonical `HOLD` view and blockers. Do not imply readiness.
- `valid=true` and advancement true for a subject: the typed contract permits that action, subject to runtime enforcement and external evidence.

The validator emits canonical delivery Markdown and its digest. Use or link that exact view so compression cannot hide blockers. `ADVANCEMENT-ALLOWED` means both that blockers are clear and that the selected action is an advancement action; a selected pause remains `HOLD`. Evidence observation must not be future-dated, and passing evidence must remain fresh at both the manifest date and the current validation date. JSON object fields use exact ordinal names and reject extra, mixed-case alias, or duplicate keys before semantic parsing. The gate proves external trust-anchor match, manifest/packet consistency, file hashes, attestation identity, and evidence binding; it does not prove that the trusted manifest author or a cited real-world observation is truthful. Keep the manifest and attestation write scope outside the producer/integrator scope.
