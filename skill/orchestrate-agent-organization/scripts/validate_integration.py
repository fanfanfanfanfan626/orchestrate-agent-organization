#!/usr/bin/env python3
"""Validate a final integration packet against an independent assurance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from datetime import date
from pathlib import Path
from typing import Any


PACKET_VERSION = "integration-v2"
MANIFEST_VERSION = "assurance-v1"
SEVERITIES = {"P0", "P1", "P2"}
OBLIGATION_STATUSES = {"open-blocker", "contested-blocker", "verified-closed"}
SAFE_ACTIONS = {
    "hold",
    "pause",
    "discovery",
    "revalidate",
    "operate-safe",
    "human-gated",
    "retire-review",
    "retire",
}
ADVANCE_ACTIONS = {"resume", "release", "scale", "cutover"}
SUBJECT_KINDS = {"product-asset", "live-investment", "external-paused-product"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
CONTROL_STATUSES = {
    "verified",
    "declared-unverified",
    "proposed",
    "missing-blocker",
    "not-applicable",
}
CONTROL_FIELDS = (
    "durable_owner",
    "on_call",
    "reconciliation",
    "support_surface",
    "slis_alerts",
    "incident_safe_state",
    "maintenance",
    "retirement",
    "next_evidence_trigger",
)
MANDATORY_HIGH_RISK_CONTROLS = {
    "durable_owner",
    "on_call",
    "slis_alerts",
    "incident_safe_state",
    "maintenance",
    "retirement",
    "next_evidence_trigger",
}
GATE_AUTHORITIES = {"human", "machine", "external"}
GATE_STATUSES = {"required", "satisfied"}
EVIDENCE_RESULTS = {"pass", "fail"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DuplicateJsonKeyError(ValueError):
    """Raised before semantic validation when a JSON object repeats a key."""


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an integration packet against an assurance manifest"
    )
    parser.add_argument("packet", help="Path to integration-v2 JSON")
    parser.add_argument("manifest", help="Path to assurance-v1 JSON")
    parser.add_argument(
        "expected_manifest_sha",
        help="Trusted manifest SHA-256 copied from the parent Charter or decision artifact",
    )
    return parser.parse_args()


def load_json_bytes(path: Path) -> tuple[Any, bytes]:
    raw = path.read_bytes()
    return json.loads(
        raw.decode("utf-8-sig"), object_pairs_hook=reject_duplicate_pairs
    ), raw


def verify_bound_file(
    reference: str,
    expected_sha: str,
    label: str,
    manifest_path: Path,
    errors: list[str],
) -> Path | None:
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label} must be a relative path inside the manifest directory")
        return None
    root = manifest_path.parent.resolve()
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            attributes = getattr(cursor.lstat(), "st_file_attributes", 0)
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if cursor.is_symlink() or attributes & reparse_flag:
                errors.append(f"{label} must not traverse reparse points")
                return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"{label} must be a relative path inside the manifest directory")
        return None
    if not candidate.is_file():
        errors.append(f"{label} file is missing or is not a regular file")
        return None
    actual_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if expected_sha and actual_sha != expected_sha:
        errors.append(f"{label} SHA-256 does not match the referenced file")
        return None
    return candidate


def verify_attestation(
    path: Path | None,
    record: dict[str, str],
    decision_id: str,
    label: str,
    errors: list[str],
) -> None:
    if path is None:
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        errors.append(f"{label} must be valid JSON")
        return
    if not isinstance(raw, dict):
        errors.append(f"{label} must be a JSON object")
        return
    expected = {
        "schema_version": "evidence-attestation-v1",
        "evidence_id": record["id"],
        "decision_id": decision_id,
        "subject_id": record["subject_id"],
        "evidence_key": record["evidence_key"],
        "scope": record["scope"],
        "decision_version": record["decision_version"],
        "check_result": record["check_result"],
        "verified_by": record["verified_by"],
        "observed_at": record["observed_at"],
        "fresh_until": record["fresh_until"],
    }
    exact_keys(raw, set(expected), label, errors)
    for field, value in expected.items():
        if raw.get(field) != value:
            errors.append(f"{label}.{field} does not match its evidence record")


def is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def required_string(
    obj: dict[str, Any], name: str, label: str, errors: list[str]
) -> str:
    value = obj.get(name)
    if not is_string(value):
        errors.append(f"{label}.{name} must be a non-empty string")
        return ""
    return value.strip()


def optional_string(
    obj: dict[str, Any], name: str, label: str, errors: list[str]
) -> str | None:
    value = obj.get(name)
    if value is None:
        return None
    if not is_string(value):
        errors.append(f"{label}.{name} must be null or a non-empty string")
        return None
    return value.strip()


def required_bool(
    obj: dict[str, Any], name: str, label: str, errors: list[str]
) -> bool:
    value = obj.get(name)
    if type(value) is not bool:
        errors.append(f"{label}.{name} must be a JSON Boolean")
        return False
    return value


def string_list(
    value: Any, label: str, errors: list[str], *, allow_empty: bool = True
) -> list[str]:
    if not isinstance(value, list) or any(not is_string(item) for item in value):
        errors.append(f"{label} must be an array of non-empty strings")
        return []
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        errors.append(f"{label} must not be empty")
    if len(result) != len(set(result)):
        errors.append(f"{label} must not contain duplicates")
    return result


def object_list(value: Any, label: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        errors.append(f"{label} must be an array of objects")
        return []
    return value


def require_enum(
    value: str, allowed: set[str], label: str, errors: list[str]
) -> None:
    if value and value not in allowed:
        errors.append(f"{label} is not allowed")


def require_sha(value: str, label: str, errors: list[str]) -> None:
    if value and SHA256_PATTERN.fullmatch(value) is None:
        errors.append(f"{label} must be a lowercase SHA-256 digest")


def parse_date(value: str, label: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be an ISO date")
        return None


def exact_keys(
    actual: dict[str, Any], expected: set[str], label: str, errors: list[str]
) -> None:
    actual_keys = set(actual)
    for missing in sorted(expected - actual_keys):
        errors.append(f"{label} is missing {missing}")
    for extra in sorted(actual_keys - expected):
        errors.append(f"{label} has unexpected field {extra}")


def build_manifest(
    raw: Any, raw_bytes: bytes, manifest_path: Path, errors: list[str]
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        errors.append("manifest must be a JSON object")
        return {}
    if raw.get("schema_version") != MANIFEST_VERSION:
        errors.append(f"manifest.schema_version must equal {MANIFEST_VERSION}")
    exact_keys(
        raw,
        {
            "schema_version",
            "manifest_id",
            "decision_id",
            "as_of",
            "authorized_verifiers",
            "findings",
            "required_subjects",
            "evidence_catalog",
        },
        "manifest",
        errors,
    )
    manifest_id = required_string(raw, "manifest_id", "manifest", errors)
    decision_id = required_string(raw, "decision_id", "manifest", errors)
    as_of_text = required_string(raw, "as_of", "manifest", errors)
    as_of = parse_date(as_of_text, "manifest.as_of", errors) if as_of_text else None
    if as_of and as_of > date.today():
        errors.append("manifest.as_of must not be in the future")
    authorized_verifiers = string_list(
        raw.get("authorized_verifiers"),
        "manifest.authorized_verifiers",
        errors,
        allow_empty=False,
    )
    findings = object_list(raw.get("findings"), "manifest.findings", errors)
    subjects = object_list(
        raw.get("required_subjects"), "manifest.required_subjects", errors
    )
    evidence = object_list(
        raw.get("evidence_catalog"), "manifest.evidence_catalog", errors
    )

    finding_map: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        label = f"manifest.findings[{index}]"
        exact_keys(
            finding,
            {
                "id",
                "severity",
                "subject_id",
                "statement",
                "required_action",
                "required_evidence_keys",
                "required_gate_ids",
            },
            label,
            errors,
        )
        finding_id = required_string(finding, "id", label, errors)
        severity = required_string(finding, "severity", label, errors)
        subject_id = required_string(finding, "subject_id", label, errors)
        statement = required_string(finding, "statement", label, errors)
        required_action = required_string(finding, "required_action", label, errors)
        evidence_keys = string_list(
            finding.get("required_evidence_keys"),
            f"{label}.required_evidence_keys",
            errors,
            allow_empty=False,
        )
        gate_ids = string_list(
            finding.get("required_gate_ids"), f"{label}.required_gate_ids", errors
        )
        require_enum(severity, SEVERITIES, f"{label}.severity", errors)
        if finding_id:
            if finding_id in finding_map:
                errors.append(f"manifest finding id {finding_id} is duplicated")
            finding_map[finding_id] = {
                "severity": severity,
                "subject_id": subject_id,
                "statement": statement,
                "required_action": required_action,
                "required_evidence_keys": evidence_keys,
                "required_gate_ids": gate_ids,
            }

    subject_map: dict[str, dict[str, Any]] = {}
    gate_map: dict[str, dict[str, Any]] = {}
    for index, subject in enumerate(subjects):
        label = f"manifest.required_subjects[{index}]"
        exact_keys(
            subject,
            {
                "subject_id",
                "subject_kind",
                "risk_level",
                "current_state",
                "money_affected",
                "accountable_owner_principal_id",
                "required_safe_action",
                "allowed_not_applicable",
                "required_authority_gates",
            },
            label,
            errors,
        )
        subject_id = required_string(subject, "subject_id", label, errors)
        subject_kind = required_string(subject, "subject_kind", label, errors)
        risk_level = required_string(subject, "risk_level", label, errors)
        current_state = required_string(subject, "current_state", label, errors)
        money_affected = required_bool(subject, "money_affected", label, errors)
        owner_principal = required_string(
            subject, "accountable_owner_principal_id", label, errors
        )
        safe_action = required_string(subject, "required_safe_action", label, errors)
        allowed_na = string_list(
            subject.get("allowed_not_applicable"),
            f"{label}.allowed_not_applicable",
            errors,
        )
        gates = object_list(
            subject.get("required_authority_gates"),
            f"{label}.required_authority_gates",
            errors,
        )
        require_enum(subject_kind, SUBJECT_KINDS, f"{label}.subject_kind", errors)
        require_enum(risk_level, RISK_LEVELS, f"{label}.risk_level", errors)
        require_enum(safe_action, SAFE_ACTIONS, f"{label}.required_safe_action", errors)
        for field in allowed_na:
            if field not in CONTROL_FIELDS:
                errors.append(f"{label}.allowed_not_applicable contains {field}")
            if field == "reconciliation" and money_affected:
                errors.append(
                    f"{label}.reconciliation cannot be not-applicable when money is affected"
                )
        if subject_id:
            if subject_id in subject_map:
                errors.append(f"manifest subject id {subject_id} is duplicated")
            subject_map[subject_id] = {
                "subject_kind": subject_kind,
                "risk_level": risk_level,
                "current_state": current_state,
                "money_affected": money_affected,
                "accountable_owner_principal_id": owner_principal,
                "required_safe_action": safe_action,
                "allowed_not_applicable": allowed_na,
            }
        for gate_index, gate in enumerate(gates):
            gate_label = f"{label}.required_authority_gates[{gate_index}]"
            exact_keys(
                gate,
                {"id", "action", "scope", "authority", "decision_version"},
                gate_label,
                errors,
            )
            gate_id = required_string(gate, "id", gate_label, errors)
            action = required_string(gate, "action", gate_label, errors)
            scope = required_string(gate, "scope", gate_label, errors)
            authority = required_string(gate, "authority", gate_label, errors)
            decision_version = required_string(
                gate, "decision_version", gate_label, errors
            )
            require_enum(action, ADVANCE_ACTIONS, f"{gate_label}.action", errors)
            require_enum(
                authority, GATE_AUTHORITIES, f"{gate_label}.authority", errors
            )
            if gate_id:
                if gate_id in gate_map:
                    errors.append(f"manifest gate id {gate_id} is duplicated")
                gate_map[gate_id] = {
                    "subject_id": subject_id,
                    "action": action,
                    "scope": scope,
                    "authority": authority,
                    "decision_version": decision_version,
                }

    for finding_id, finding in finding_map.items():
        if finding["subject_id"] not in subject_map:
            errors.append(f"manifest finding {finding_id} references unknown subject")
        for gate_id in finding["required_gate_ids"]:
            gate = gate_map.get(gate_id)
            if gate is None:
                errors.append(f"manifest finding {finding_id} references unknown gate")
            elif gate["subject_id"] != finding["subject_id"]:
                errors.append(f"manifest finding {finding_id} gate subject differs")

    evidence_map: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(evidence):
        label = f"manifest.evidence_catalog[{index}]"
        exact_keys(
            record,
            {
                "id",
                "evidence_key",
                "subject_id",
                "artifact_ref",
                "artifact_sha256",
                "check_result",
                "scope",
                "decision_version",
                "observed_at",
                "fresh_until",
                "verified_by",
                "attestation_ref",
                "attestation_sha256",
            },
            label,
            errors,
        )
        evidence_id = required_string(record, "id", label, errors)
        evidence_key = required_string(record, "evidence_key", label, errors)
        subject_id = required_string(record, "subject_id", label, errors)
        artifact_ref = required_string(record, "artifact_ref", label, errors)
        artifact_sha = required_string(record, "artifact_sha256", label, errors)
        check_result = required_string(record, "check_result", label, errors)
        scope = required_string(record, "scope", label, errors)
        decision_version = required_string(
            record, "decision_version", label, errors
        )
        observed_text = required_string(record, "observed_at", label, errors)
        fresh_text = required_string(record, "fresh_until", label, errors)
        verified_by = required_string(record, "verified_by", label, errors)
        attestation_ref = required_string(record, "attestation_ref", label, errors)
        attestation_sha = required_string(
            record, "attestation_sha256", label, errors
        )
        require_sha(artifact_sha, f"{label}.artifact_sha256", errors)
        require_sha(attestation_sha, f"{label}.attestation_sha256", errors)
        require_enum(check_result, EVIDENCE_RESULTS, f"{label}.check_result", errors)
        observed = parse_date(observed_text, f"{label}.observed_at", errors)
        fresh = parse_date(fresh_text, f"{label}.fresh_until", errors)
        if observed and fresh and fresh < observed:
            errors.append(f"{label}.fresh_until precedes observed_at")
        if observed and as_of and observed > as_of:
            errors.append(f"{label}.observed_at is after manifest.as_of")
        if observed and observed > date.today():
            errors.append(f"{label}.observed_at is after validation date")
        if check_result == "pass" and as_of and fresh and fresh < as_of:
            errors.append(f"{label}.passing evidence is stale at manifest.as_of")
        if check_result == "pass" and fresh and fresh < date.today():
            errors.append(f"{label}.passing evidence is stale at validation date")
        if verified_by and verified_by not in authorized_verifiers:
            errors.append(f"{label}.verified_by is not an authorized verifier")
        if subject_id and subject_id not in subject_map:
            errors.append(f"{label}.subject_id is not a required subject")
        artifact_path = verify_bound_file(
            artifact_ref,
            artifact_sha,
            f"{label}.artifact_ref",
            manifest_path,
            errors,
        )
        attestation_path = verify_bound_file(
            attestation_ref,
            attestation_sha,
            f"{label}.attestation_ref",
            manifest_path,
            errors,
        )
        verify_attestation(
            attestation_path,
            {
                "id": evidence_id,
                "subject_id": subject_id,
                "evidence_key": evidence_key,
                "scope": scope,
                "decision_version": decision_version,
                "check_result": check_result,
                "verified_by": verified_by,
                "observed_at": observed_text,
                "fresh_until": fresh_text,
            },
            decision_id,
            f"{label}.attestation",
            errors,
        )
        if evidence_id:
            if evidence_id in evidence_map:
                errors.append(f"manifest evidence id {evidence_id} is duplicated")
            evidence_map[evidence_id] = {
                "evidence_key": evidence_key,
                "subject_id": subject_id,
                "artifact_ref": artifact_ref,
                "artifact_sha256": artifact_sha,
                "check_result": check_result,
                "scope": scope,
                "decision_version": decision_version,
                "observed_at": observed_text,
                "fresh_until": fresh_text,
                "verified_by": verified_by,
                "attestation_ref": attestation_ref,
                "attestation_sha256": attestation_sha,
            }

    return {
        "manifest_id": manifest_id,
        "decision_id": decision_id,
        "as_of": as_of_text,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "authorized_verifiers": authorized_verifiers,
        "findings": finding_map,
        "subjects": subject_map,
        "gates": gate_map,
        "evidence": evidence_map,
    }


def evidence_refs(
    value: Any,
    label: str,
    manifest: dict[str, Any],
    errors: list[str],
) -> list[str]:
    refs = string_list(value, label, errors)
    for ref in refs:
        if ref not in manifest.get("evidence", {}):
            errors.append(f"{label} references unknown manifest evidence {ref}")
    return refs


def evidence_covers(
    refs: list[str],
    required_keys: list[str],
    subject_id: str,
    manifest: dict[str, Any],
    *,
    verifier: str | None = None,
    scope: str | None = None,
    decision_version: str | None = None,
) -> bool:
    records = [
        manifest["evidence"][ref]
        for ref in refs
        if ref in manifest["evidence"]
        and manifest["evidence"][ref]["check_result"] == "pass"
        and manifest["evidence"][ref]["subject_id"] == subject_id
        and (verifier is None or manifest["evidence"][ref]["verified_by"] == verifier)
        and (scope is None or manifest["evidence"][ref]["scope"] == scope)
        and (
            decision_version is None
            or manifest["evidence"][ref]["decision_version"] == decision_version
        )
    ]
    covered = {record["evidence_key"] for record in records}
    return set(required_keys).issubset(covered)


def evidence_rationale(refs: list[str]) -> str:
    return "Verified by manifest evidence: " + ", ".join(refs)


def canonical_delivery(
    decision_id: str,
    manifest_id: str,
    manifest_sha: str,
    subjects: dict[str, dict[str, Any]],
) -> str:
    lines = [
        f"# Integration decision: {decision_id}",
        f"Manifest: {manifest_id} @ sha256:{manifest_sha}",
        "",
    ]
    for subject_id in sorted(subjects):
        subject = subjects[subject_id]
        verdict = (
            "ADVANCEMENT-ALLOWED" if subject["advancement_allowed"] else "HOLD"
        )
        lines.append(
            f"- {subject_id}: {verdict}; action={subject['recommended_action']}"
        )
        lines.append(
            "  - Open P0/P1: "
            + (", ".join(subject["open_high"]) if subject["open_high"] else "none")
        )
        lines.append(
            "  - Blocking controls: "
            + (
                ", ".join(subject["blocking_controls"])
                if subject["blocking_controls"]
                else "none"
            )
        )
        lines.append(
            "  - Unsatisfied gates: "
            + (
                ", ".join(subject["unsatisfied_gates"])
                if subject["unsatisfied_gates"]
                else "none"
            )
        )
    return "\n".join(lines) + "\n"


def validate_packet(
    raw: Any,
    manifest: dict[str, Any],
    expected_manifest_sha: str,
    errors: list[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    if not isinstance(raw, dict):
        errors.append("packet must be a JSON object")
        return {}
    if raw.get("schema_version") != PACKET_VERSION:
        errors.append(f"packet.schema_version must equal {PACKET_VERSION}")
    exact_keys(
        raw,
        {
            "schema_version",
            "decision_id",
            "assurance_manifest",
            "review_findings",
            "obligations",
            "operating_controls",
            "authority_gates",
        },
        "packet",
        errors,
    )
    decision_id = required_string(raw, "decision_id", "packet", errors)
    binding = raw.get("assurance_manifest")
    if not isinstance(binding, dict):
        errors.append("packet.assurance_manifest must be an object")
        binding = {}
    exact_keys(binding, {"id", "sha256"}, "packet.assurance_manifest", errors)
    binding_id = required_string(binding, "id", "packet.assurance_manifest", errors)
    binding_sha = required_string(
        binding, "sha256", "packet.assurance_manifest", errors
    )
    require_sha(binding_sha, "packet.assurance_manifest.sha256", errors)
    if binding_id != manifest.get("manifest_id"):
        errors.append("packet assurance manifest id does not match source manifest")
    if binding_sha != manifest.get("sha256"):
        errors.append("packet assurance manifest SHA-256 does not match source manifest")
    if decision_id != manifest.get("decision_id"):
        errors.append("packet decision_id does not match source manifest")

    findings = object_list(raw.get("review_findings"), "review_findings", errors)
    obligations = object_list(raw.get("obligations"), "obligations", errors)
    control_packets = object_list(
        raw.get("operating_controls"), "operating_controls", errors
    )
    gates = object_list(raw.get("authority_gates"), "authority_gates", errors)

    packet_findings: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        label = f"review_findings[{index}]"
        exact_keys(
            finding,
            {
                "id",
                "severity",
                "subject_id",
                "statement",
                "required_action",
                "required_evidence_keys",
                "required_gate_ids",
            },
            label,
            errors,
        )
        finding_id = required_string(finding, "id", label, errors)
        severity = required_string(finding, "severity", label, errors)
        subject_id = required_string(finding, "subject_id", label, errors)
        statement = required_string(finding, "statement", label, errors)
        required_action = required_string(finding, "required_action", label, errors)
        evidence_keys = string_list(
            finding.get("required_evidence_keys"),
            f"{label}.required_evidence_keys",
            errors,
            allow_empty=False,
        )
        gate_ids = string_list(
            finding.get("required_gate_ids"), f"{label}.required_gate_ids", errors
        )
        require_enum(severity, SEVERITIES, f"{label}.severity", errors)
        if finding_id:
            if finding_id in packet_findings:
                errors.append(f"review finding id {finding_id} is duplicated")
            packet_findings[finding_id] = {
                "severity": severity,
                "subject_id": subject_id,
                "statement": statement,
                "required_action": required_action,
                "required_evidence_keys": evidence_keys,
                "required_gate_ids": gate_ids,
            }

    if set(packet_findings) != set(manifest.get("findings", {})):
        errors.append("packet review finding IDs do not exactly match source manifest")
    for finding_id, source in manifest.get("findings", {}).items():
        if finding_id in packet_findings and packet_findings[finding_id] != source:
            errors.append(f"review finding {finding_id} differs from source manifest")

    packet_gates: dict[str, dict[str, Any]] = {}
    for index, gate in enumerate(gates):
        label = f"authority_gates[{index}]"
        exact_keys(
            gate,
            {
                "id",
                "subject_id",
                "action",
                "scope",
                "authority",
                "decision_version",
                "status",
                "evidence_refs",
                "rationale",
            },
            label,
            errors,
        )
        gate_id = required_string(gate, "id", label, errors)
        subject_id = required_string(gate, "subject_id", label, errors)
        action = required_string(gate, "action", label, errors)
        scope = required_string(gate, "scope", label, errors)
        authority = required_string(gate, "authority", label, errors)
        decision_version = required_string(
            gate, "decision_version", label, errors
        )
        status = required_string(gate, "status", label, errors)
        refs = evidence_refs(
            gate.get("evidence_refs"), f"{label}.evidence_refs", manifest, errors
        )
        rationale = required_string(gate, "rationale", label, errors)
        require_enum(action, ADVANCE_ACTIONS, f"{label}.action", errors)
        require_enum(authority, GATE_AUTHORITIES, f"{label}.authority", errors)
        require_enum(status, GATE_STATUSES, f"{label}.status", errors)
        source_shape = {
            "subject_id": subject_id,
            "action": action,
            "scope": scope,
            "authority": authority,
            "decision_version": decision_version,
        }
        if gate_id:
            if gate_id in packet_gates:
                errors.append(f"authority gate id {gate_id} is duplicated")
            packet_gates[gate_id] = {**source_shape, "status": status, "refs": refs}
        if status == "satisfied" and not evidence_covers(
            refs,
            [f"gate:{gate_id}"],
            subject_id,
            manifest,
            scope=scope,
            decision_version=decision_version,
        ):
            errors.append(f"{label}.satisfied gate lacks matching manifest evidence")
        if status == "satisfied" and rationale != evidence_rationale(refs):
            errors.append(f"{label}.satisfied gate rationale is not canonical")
        source = manifest.get("gates", {}).get(gate_id)
        if source is not None and source_shape != source:
            errors.append(f"authority gate {gate_id} differs from source manifest")

    if set(packet_gates) != set(manifest.get("gates", {})):
        errors.append("packet authority gate IDs do not exactly match source manifest")

    obligation_map: dict[str, dict[str, Any]] = {}
    for index, obligation in enumerate(obligations):
        label = f"obligations[{index}]"
        exact_keys(
            obligation,
            {
                "finding_id",
                "severity",
                "subject_id",
                "preserved_requirement",
                "status",
                "owner_principal_id",
                "required_evidence_keys",
                "required_gate_ids",
                "evidence_refs",
                "verified_by",
                "safe_action_if_open",
            },
            label,
            errors,
        )
        finding_id = required_string(obligation, "finding_id", label, errors)
        severity = required_string(obligation, "severity", label, errors)
        subject_id = required_string(obligation, "subject_id", label, errors)
        preserved = required_string(
            obligation, "preserved_requirement", label, errors
        )
        status = required_string(obligation, "status", label, errors)
        owner = required_string(obligation, "owner_principal_id", label, errors)
        required_keys = string_list(
            obligation.get("required_evidence_keys"),
            f"{label}.required_evidence_keys",
            errors,
            allow_empty=False,
        )
        required_gate_ids = string_list(
            obligation.get("required_gate_ids"),
            f"{label}.required_gate_ids",
            errors,
        )
        refs = evidence_refs(
            obligation.get("evidence_refs"),
            f"{label}.evidence_refs",
            manifest,
            errors,
        )
        verified_by = optional_string(obligation, "verified_by", label, errors)
        safe_action = optional_string(
            obligation, "safe_action_if_open", label, errors
        )
        require_enum(severity, SEVERITIES, f"{label}.severity", errors)
        require_enum(status, OBLIGATION_STATUSES, f"{label}.status", errors)
        source = manifest.get("findings", {}).get(finding_id)
        if source is None and finding_id:
            errors.append(f"obligation {finding_id} has no source finding")
        elif source is not None:
            if severity != source["severity"]:
                errors.append(f"obligation {finding_id} changes finding severity")
            if subject_id != source["subject_id"]:
                errors.append(f"obligation {finding_id} changes finding subject")
            if preserved != source["required_action"]:
                errors.append(f"obligation {finding_id} changes required_action")
            if required_keys != source["required_evidence_keys"]:
                errors.append(f"obligation {finding_id} changes required evidence")
            if required_gate_ids != source["required_gate_ids"]:
                errors.append(f"obligation {finding_id} changes required gates")
        if finding_id:
            if finding_id in obligation_map:
                errors.append(f"obligation for finding {finding_id} is duplicated")
            obligation_map[finding_id] = {
                "severity": severity,
                "subject_id": subject_id,
                "status": status,
                "safe_action": safe_action,
            }
        for gate_id in required_gate_ids:
            if gate_id not in packet_gates:
                errors.append(f"{label} references missing authority gate {gate_id}")
        subject = manifest.get("subjects", {}).get(subject_id, {})
        if owner != subject.get("accountable_owner_principal_id"):
            errors.append(f"{label}.owner principal differs from source manifest")
        if status in {"open-blocker", "contested-blocker"}:
            if safe_action != subject.get("required_safe_action"):
                errors.append(f"{label}.safe action conflicts with source manifest")
            if status == "contested-blocker" and not refs:
                errors.append(f"{label}.contested blocker requires manifest evidence")
        elif status == "verified-closed":
            if safe_action is not None:
                errors.append(
                    f"{label}.verified closure must set safe_action_if_open to null"
                )
            if verified_by not in manifest.get("authorized_verifiers", []):
                errors.append(f"{label}.verified_by is not authorized by manifest")
            if severity in {"P0", "P1"} and verified_by == owner:
                errors.append(f"{label}.P0/P1 closure is not independent")
            if not evidence_covers(
                refs,
                required_keys,
                subject_id,
                manifest,
                verifier=verified_by,
            ):
                errors.append(
                    f"{label}.closure does not cover every required evidence key"
                )

    if set(obligation_map) != set(manifest.get("findings", {})):
        errors.append("packet obligation IDs do not exactly match source findings")

    subject_results: dict[str, dict[str, Any]] = {}
    packet_subject_ids: set[str] = set()
    for index, packet in enumerate(control_packets):
        label = f"operating_controls[{index}]"
        exact_keys(
            packet,
            {
                "subject_id",
                "subject_kind",
                "risk_level",
                "current_state",
                "recommended_action",
                "money_affected",
                "accountable_owner_principal_id",
                "controls",
            },
            label,
            errors,
        )
        subject_id = required_string(packet, "subject_id", label, errors)
        subject_kind = required_string(packet, "subject_kind", label, errors)
        risk_level = required_string(packet, "risk_level", label, errors)
        current_state = required_string(packet, "current_state", label, errors)
        recommended_action = required_string(
            packet, "recommended_action", label, errors
        )
        money_affected = required_bool(packet, "money_affected", label, errors)
        owner_principal = required_string(
            packet, "accountable_owner_principal_id", label, errors
        )
        controls = packet.get("controls")
        require_enum(subject_kind, SUBJECT_KINDS, f"{label}.subject_kind", errors)
        require_enum(risk_level, RISK_LEVELS, f"{label}.risk_level", errors)
        require_enum(
            recommended_action,
            SAFE_ACTIONS | ADVANCE_ACTIONS,
            f"{label}.recommended_action",
            errors,
        )
        source = manifest.get("subjects", {}).get(subject_id)
        if source is None and subject_id:
            errors.append(f"{label}.subject_id is not required by source manifest")
            source = {}
        elif source is not None:
            for name, value in {
                "subject_kind": subject_kind,
                "risk_level": risk_level,
                "current_state": current_state,
                "money_affected": money_affected,
                "accountable_owner_principal_id": owner_principal,
            }.items():
                if value != source[name]:
                    errors.append(f"{label}.{name} differs from source manifest")
        if subject_id in packet_subject_ids:
            errors.append(f"operating control subject {subject_id} is duplicated")
        packet_subject_ids.add(subject_id)
        if not isinstance(controls, dict):
            errors.append(f"{label}.controls must be an object")
            controls = {}
        exact_keys(controls, set(CONTROL_FIELDS), f"{label}.controls", errors)
        control_states: dict[str, str] = {}
        blocking_fields: list[str] = []
        for field in CONTROL_FIELDS:
            field_label = f"{label}.controls.{field}"
            control = controls.get(field)
            if not isinstance(control, dict):
                errors.append(f"{field_label} must be an object")
                continue
            exact_keys(
                control,
                {"status", "evidence_refs", "rationale"},
                field_label,
                errors,
            )
            status = required_string(control, "status", field_label, errors)
            refs = evidence_refs(
                control.get("evidence_refs"),
                f"{field_label}.evidence_refs",
                manifest,
                errors,
            )
            rationale = required_string(control, "rationale", field_label, errors)
            require_enum(status, CONTROL_STATUSES, f"{field_label}.status", errors)
            if status == "verified" and not evidence_covers(
                refs,
                [f"control:{field}"],
                subject_id,
                manifest,
            ):
                errors.append(
                    f"{field_label}.verified control lacks matching manifest evidence"
                )
            if status == "verified" and rationale != evidence_rationale(refs):
                errors.append(
                    f"{field_label}.verified control rationale is not canonical"
                )
            if status == "not-applicable" and field not in source.get(
                "allowed_not_applicable", []
            ):
                errors.append(
                    f"{field_label}.not-applicable is not allowed by source manifest"
                )
            if status == "not-applicable" and risk_level in {"high", "critical"}:
                mandatory = field in MANDATORY_HIGH_RISK_CONTROLS or (
                    field == "support_surface"
                    and subject_kind in {"product-asset", "external-paused-product"}
                ) or (field == "reconciliation" and money_affected)
                if mandatory:
                    errors.append(
                        f"{field_label}.not-applicable violates the high-risk applicability matrix"
                    )
            if status in {
                "declared-unverified",
                "proposed",
                "missing-blocker",
            }:
                blocking_fields.append(field)
            control_states[field] = status

        open_high = sorted(
            finding_id
            for finding_id, obligation in obligation_map.items()
            if obligation["subject_id"] == subject_id
            and obligation["severity"] in {"P0", "P1"}
            and obligation["status"] != "verified-closed"
        )
        unsatisfied = sorted(
            gate_id
            for gate_id, gate in packet_gates.items()
            if gate["subject_id"] == subject_id and gate["status"] == "required"
        )
        blockers = bool(open_high or blocking_fields or unsatisfied)
        advancement_allowed = not blockers and recommended_action in ADVANCE_ACTIONS
        required_safe_action = source.get("required_safe_action")
        if recommended_action in SAFE_ACTIONS and recommended_action != required_safe_action:
            errors.append(f"{label}.safe action conflicts with source manifest")
        if blockers and recommended_action != required_safe_action:
            errors.append(f"{label}.blockers require the manifest safe action")
        if recommended_action in ADVANCE_ACTIONS and blockers:
            errors.append(f"{label} attempts advancement while blockers remain")
        subject_gates = [
            gate for gate in packet_gates.values() if gate["subject_id"] == subject_id
        ]
        if (
            recommended_action in ADVANCE_ACTIONS
            and subject_gates
            and not any(gate["action"] == recommended_action for gate in subject_gates)
        ):
            errors.append(f"{label}.advancement action lacks an exact manifest gate")
        if recommended_action in ADVANCE_ACTIONS and risk_level in {"high", "critical"}:
            if any(
                state not in {"verified", "not-applicable"}
                for state in control_states.values()
            ):
                errors.append(f"{label}.high-risk advancement lacks verified controls")
        if blockers:
            warnings.append(
                f"{subject_id} remains non-advancing until manifest-bound blockers close"
            )
        subject_results[subject_id or label] = {
            "recommended_action": recommended_action,
            "advancement_allowed": advancement_allowed,
            "open_high": open_high,
            "blocking_controls": sorted(blocking_fields),
            "unsatisfied_gates": unsatisfied,
        }

    if packet_subject_ids != set(manifest.get("subjects", {})):
        errors.append("packet operating-control subjects do not exactly match manifest")

    valid = not errors
    delivery = None
    delivery_sha = None
    if valid:
        delivery = canonical_delivery(
            decision_id,
            manifest["manifest_id"],
            manifest["sha256"],
            subject_results,
        )
        delivery_sha = hashlib.sha256(delivery.encode("utf-8")).hexdigest()
    return {
        "valid": valid,
        "schema_version": PACKET_VERSION,
        "manifest_version": MANIFEST_VERSION,
        "decision_id": decision_id,
        "manifest_id": manifest.get("manifest_id", ""),
        "manifest_sha256": manifest.get("sha256", ""),
        "expected_manifest_sha256": expected_manifest_sha,
        "advancement_allowed_by_subject": {
            key: bool(valid and value["advancement_allowed"])
            for key, value in sorted(subject_results.items())
        },
        "open_high_severity_obligations": sorted(
            {
                finding
                for subject in subject_results.values()
                for finding in subject["open_high"]
            }
        ),
        "blocking_control_fields": sorted(
            {
                f"{subject_id}:{field}"
                for subject_id, subject in subject_results.items()
                for field in subject["blocking_controls"]
            }
        ),
        "unsatisfied_authority_gates": sorted(
            {
                gate
                for subject in subject_results.values()
                for gate in subject["unsatisfied_gates"]
            }
        ),
        "canonical_delivery_markdown": delivery,
        "canonical_delivery_sha256": delivery_sha,
        "errors": errors,
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    try:
        manifest_raw, manifest_bytes = load_json_bytes(Path(args.manifest))
        manifest = build_manifest(
            manifest_raw, manifest_bytes, Path(args.manifest), errors
        )
        require_sha(
            args.expected_manifest_sha,
            "expected_manifest_sha",
            errors,
        )
        if args.expected_manifest_sha != manifest.get("sha256"):
            errors.append("source manifest SHA-256 does not match external trust anchor")
        packet_raw, _ = load_json_bytes(Path(args.packet))
        result = validate_packet(
            packet_raw, manifest, args.expected_manifest_sha, errors
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateJsonKeyError,
    ) as exc:
        result = {
            "valid": False,
            "schema_version": PACKET_VERSION,
            "manifest_version": MANIFEST_VERSION,
            "errors": [str(exc)],
            "warnings": [],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid") else 2


if __name__ == "__main__":
    raise SystemExit(main())
