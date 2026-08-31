#!/usr/bin/env python3
"""Validate persistent studio state and recommend bounded portfolio actions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


COMPANY_POLICY_VERSION = "company-v5"
PLANNER_VERSION = "studio-portfolio-v2"
PORTFOLIO_STATES = {
    "opportunity", "discovery", "funded", "build", "operate", "scale", "pause", "retire",
}
FOUNDER_STATUSES = {
    "not-required", "raw", "framed", "explored", "decision-ready", "authorized",
}
CAPABILITY_STATUSES = {"candidate", "validated", "degraded", "retired"}
ASSET_STATES = {"operate", "scale", "pause", "retire"}
EVIDENCE_CLASSES = {
    "external-outcome", "production-observation", "controlled-experiment",
    "executable-test", "source-analysis", "agent-claim",
}
ENVELOPE_KEYS = (
    "investment_units", "human_attention_units", "maintenance_units", "risk_capacity_units",
)
ACTIVE_INVESTMENT_STATES = {"funded", "build", "scale"}
ALLOWED_TRANSITIONS = {
    "opportunity": {"opportunity", "discovery", "pause", "retire"},
    "discovery": {"discovery", "funded", "pause", "retire"},
    "funded": {"funded", "discovery", "build", "pause", "retire"},
    "build": {"build", "discovery", "operate", "pause", "retire"},
    "operate": {"operate", "scale", "pause", "retire"},
    "scale": {"scale", "operate", "pause", "retire"},
    "pause": {"pause", "discovery", "funded", "build", "operate", "retire"},
    "retire": {"retire"},
}


def fail(message: str) -> None:
    raise ValueError(message)


def strict_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{name} must be a boolean")
    return value


def bounded_int(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(f"{name} must be an integer")
    if not low <= value <= high:
        fail(f"{name} must be between {low} and {high}")
    return value


def non_empty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{name} must be a non-empty string")
    return value.strip()


def optional_string(value: Any, name: str) -> str | None:
    if value is None:
        return None
    return non_empty_string(value, name)


def iso_date(value: Any, name: str) -> date:
    text = non_empty_string(value, name)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        fail(f"{name} must use YYYY-MM-DD")
    if parsed.isoformat() != text:
        fail(f"{name} must use YYYY-MM-DD")
    return parsed


def string_list(value: Any, name: str, *, non_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        fail(f"{name} must be an array of non-empty strings")
    result = [item.strip() for item in value]
    if len(set(result)) != len(result):
        fail(f"{name} must not contain duplicates")
    if non_empty and not result:
        fail(f"{name} must contain at least one item")
    return result


def object_list(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        fail(f"{name} must be an array of objects")
    return value


def envelope(value: Any, name: str) -> dict[str, int]:
    if not isinstance(value, dict):
        fail(f"{name} must be an object")
    limits = {
        "investment_units": 1000,
        "human_attention_units": 1000,
        "maintenance_units": 1000,
        "risk_capacity_units": 1000,
    }
    return {
        key: bounded_int(value.get(key, 0), f"{name}.{key}", 0, limits[key])
        for key in ENVELOPE_KEYS
    }


def indexed_objects(
    values: list[dict[str, Any]], name: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(values):
        item_id = non_empty_string(value.get("id"), f"{name}[{index}].id")
        if item_id in result:
            fail(f"duplicate {name} id: {item_id}")
        result[item_id] = value
    return result


def normalize_asset(asset_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    state = raw.get("lifecycle_state")
    if state not in ASSET_STATES:
        fail(f"asset {asset_id}.lifecycle_state is not allowed")
    result = {
        "id": asset_id,
        "lifecycle_state": state,
        "owner_seat_id": non_empty_string(raw.get("owner_seat_id"), f"asset {asset_id}.owner_seat_id"),
        "custodian_agent_id": optional_string(raw.get("custodian_agent_id"), f"asset {asset_id}.custodian_agent_id"),
        "custody_lease_expires_at": optional_string(raw.get("custody_lease_expires_at"), f"asset {asset_id}.custody_lease_expires_at"),
        "feedback_channel_ref": non_empty_string(raw.get("feedback_channel_ref"), f"asset {asset_id}.feedback_channel_ref"),
        "observability_ref": non_empty_string(raw.get("observability_ref"), f"asset {asset_id}.observability_ref"),
        "incident_route_ref": non_empty_string(raw.get("incident_route_ref"), f"asset {asset_id}.incident_route_ref"),
        "safe_state_ref": non_empty_string(raw.get("safe_state_ref"), f"asset {asset_id}.safe_state_ref"),
        "retirement_plan_ref": non_empty_string(raw.get("retirement_plan_ref"), f"asset {asset_id}.retirement_plan_ref"),
        "maintenance_units": bounded_int(raw.get("maintenance_units", 0), f"asset {asset_id}.maintenance_units", 0, 1000),
        "evidence_fresh": strict_bool(raw.get("evidence_fresh"), f"asset {asset_id}.evidence_fresh"),
        "review_triggers": string_list(raw.get("review_triggers"), f"asset {asset_id}.review_triggers", non_empty=True),
    }
    if bool(result["custodian_agent_id"]) != bool(result["custody_lease_expires_at"]):
        fail(f"asset {asset_id} custodian_agent_id and custody_lease_expires_at must appear together")
    return result


def normalize_reality_evidence(evidence_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    evidence_class = raw.get("evidence_class")
    if evidence_class not in EVIDENCE_CLASSES:
        fail(f"reality evidence {evidence_id}.evidence_class is not allowed")
    non_empty_string(raw.get("source_ref"), f"reality evidence {evidence_id}.source_ref")
    observed_at = iso_date(raw.get("observed_at"), f"reality evidence {evidence_id}.observed_at")
    fresh_until = iso_date(raw.get("fresh_until"), f"reality evidence {evidence_id}.fresh_until")
    if fresh_until < observed_at:
        fail(f"reality evidence {evidence_id}.fresh_until cannot precede observed_at")
    non_empty_string(raw.get("claim"), f"reality evidence {evidence_id}.claim")
    producer_controls_source = strict_bool(
        raw.get("producer_controls_source", False),
        f"reality evidence {evidence_id}.producer_controls_source",
    )
    confidence = bounded_int(
        raw.get("confidence", 0), f"reality evidence {evidence_id}.confidence", 0, 5
    )
    return {
        "evidence_class": evidence_class,
        "observed_at": observed_at,
        "fresh_until": fresh_until,
        "producer_controls_source": producer_controls_source,
        "confidence": confidence,
    }


def validate_capability(capability_id: str, raw: dict[str, Any]) -> None:
    status = raw.get("status")
    if status not in CAPABILITY_STATUSES:
        fail(f"capability {capability_id}.status is not allowed")
    evidence_count = bounded_int(
        raw.get("cross_task_evidence_count", 0),
        f"capability {capability_id}.cross_task_evidence_count",
        0,
        1000,
    )
    reviewed = strict_bool(
        raw.get("independent_reviewed", False),
        f"capability {capability_id}.independent_reviewed",
    )
    evidence_refs = string_list(
        raw.get("evidence_refs", []), f"capability {capability_id}.evidence_refs"
    )
    string_list(
        raw.get("known_limitations", []),
        f"capability {capability_id}.known_limitations",
    )
    optional_string(raw.get("last_validated_at"), f"capability {capability_id}.last_validated_at")
    if status == "validated":
        if evidence_count < 2 or len(evidence_refs) < 2 or not reviewed:
            fail(
                f"capability {capability_id} cannot be validated without two cross-task evidence records and independent review"
            )


def normalize_item(
    item_id: str, raw: dict[str, Any], assets: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    state = raw.get("current_state")
    if state not in PORTFOLIO_STATES:
        fail(f"{item_id}.current_state is not allowed")
    previous = raw.get("previous_state")
    if previous is not None:
        if previous not in PORTFOLIO_STATES:
            fail(f"{item_id}.previous_state is not allowed")
        if state not in ALLOWED_TRANSITIONS[previous]:
            fail(f"{item_id} transition {previous} -> {state} is not allowed")

    founder_status = raw.get("founder_charter_status", "not-required")
    if founder_status not in FOUNDER_STATUSES:
        fail(f"{item_id}.founder_charter_status is not allowed")
    founder_ref = optional_string(raw.get("founder_charter_ref"), f"{item_id}.founder_charter_ref")
    if founder_status != "not-required" and founder_ref is None:
        fail(f"{item_id}.founder_charter_ref is required for a Founder-governed item")
    if state == "build" and founder_status != "authorized":
        fail(f"{item_id} cannot be in build before Founder Charter authorization")

    asset_id = optional_string(raw.get("asset_id"), f"{item_id}.asset_id")
    if state in {"operate", "scale", "pause"}:
        if asset_id is None or asset_id not in assets:
            fail(f"{item_id} in {state} requires an existing product asset")
    if asset_id is not None and asset_id not in assets:
        fail(f"{item_id}.asset_id does not exist")

    result = {
        "id": item_id,
        "title": non_empty_string(raw.get("title"), f"{item_id}.title"),
        "current_state": state,
        "previous_state": previous,
        "founder_charter_status": founder_status,
        "founder_charter_ref": founder_ref,
        "mandatory_human_gate": strict_bool(raw.get("mandatory_human_gate", False), f"{item_id}.mandatory_human_gate"),
        "stop_condition_triggered": strict_bool(raw.get("stop_condition_triggered", False), f"{item_id}.stop_condition_triggered"),
        "evidence_fresh": strict_bool(raw.get("evidence_fresh", False), f"{item_id}.evidence_fresh"),
        "owner_seat_id": non_empty_string(raw.get("owner_seat_id"), f"{item_id}.owner_seat_id"),
        "asset_id": asset_id,
        "strategic_alignment": bounded_int(raw.get("strategic_alignment", 0), f"{item_id}.strategic_alignment", 0, 5),
        "user_evidence": bounded_int(raw.get("user_evidence", 0), f"{item_id}.user_evidence", 0, 5),
        "outcome_evidence": bounded_int(raw.get("outcome_evidence", 0), f"{item_id}.outcome_evidence", 0, 5),
        "urgency": bounded_int(raw.get("urgency", 0), f"{item_id}.urgency", 0, 5),
        "option_value": bounded_int(raw.get("option_value", 0), f"{item_id}.option_value", 0, 5),
        "confidence": bounded_int(raw.get("confidence", 0), f"{item_id}.confidence", 0, 5),
        "risk": bounded_int(raw.get("risk", 0), f"{item_id}.risk", 0, 5),
        "reversibility": bounded_int(raw.get("reversibility", 0), f"{item_id}.reversibility", 0, 5),
        "investment_units": bounded_int(raw.get("investment_units", 0), f"{item_id}.investment_units", 0, 1000),
        "human_attention_units": bounded_int(raw.get("human_attention_units", 0), f"{item_id}.human_attention_units", 0, 1000),
        "maintenance_units": bounded_int(raw.get("maintenance_units", 0), f"{item_id}.maintenance_units", 0, 1000),
        "risk_capacity_units": bounded_int(raw.get("risk_capacity_units", 0), f"{item_id}.risk_capacity_units", 0, 1000),
        "reality_evidence_refs": string_list(raw.get("reality_evidence_refs", []), f"{item_id}.reality_evidence_refs"),
        "stop_conditions": string_list(raw.get("stop_conditions"), f"{item_id}.stop_conditions", non_empty=True),
        "review_triggers": string_list(raw.get("review_triggers"), f"{item_id}.review_triggers", non_empty=True),
        "next_evidence_action": non_empty_string(raw.get("next_evidence_action"), f"{item_id}.next_evidence_action"),
    }

    if state == "scale":
        if not result["evidence_fresh"] or result["outcome_evidence"] < 4 or not result["reality_evidence_refs"]:
            fail(f"{item_id} cannot be in scale without fresh externally grounded outcome evidence")
    return result


def priority_score(item: dict[str, Any]) -> int:
    return (
        4 * item["strategic_alignment"]
        + 3 * item["user_evidence"]
        + 4 * item["outcome_evidence"]
        + 2 * item["urgency"]
        + 2 * item["option_value"]
        + item["confidence"]
        + 2 * item["reversibility"]
        - 3 * item["risk"]
        - item["investment_units"]
        - 2 * item["maintenance_units"]
        - 2 * item["human_attention_units"]
    )


def base_decision(item: dict[str, Any]) -> tuple[str, str, bool, list[str]]:
    state = item["current_state"]
    reasons: list[str] = []
    if state == "retire":
        return "retain-retired", "retire", True, ["Retired work is not silently resurrected."]
    if item["mandatory_human_gate"]:
        return "human-gated", state, True, ["A mandatory human gate is unresolved."]
    if item["stop_condition_triggered"]:
        if state == "pause":
            return "retire-review", "pause", True, ["A stop condition remains triggered while paused."]
        return "pause", "pause", True, ["A recorded stop condition is triggered."]
    if state in {"operate", "scale"} and not item["evidence_fresh"]:
        return "revalidate", state, True, ["Operating evidence is stale."]
    if state == "operate":
        if item["outcome_evidence"] <= 1 and item["reality_evidence_refs"]:
            return "pause", "pause", True, ["Fresh reality evidence shows weak outcome."]
        if (
            item["outcome_evidence"] >= 4
            and item["user_evidence"] >= 3
            and item["risk"] <= 2
            and item["has_qualifying_external_outcome"]
        ):
            return "scale-candidate", "scale", False, ["Fresh operating evidence supports a scale review."]
        return "continue", "operate", True, ["Continue bounded operation and observation."]
    if state == "scale":
        if item["outcome_evidence"] < 3 or item["risk"] >= 4:
            return "pause", "pause", True, ["Scale evidence or risk no longer supports expansion."]
        return "continue", "scale", True, ["Continue the current scale horizon."]
    if state == "pause":
        if item["evidence_fresh"] and item["founder_charter_status"] == "authorized":
            return "resume-review", "pause", True, ["Fresh evidence permits a governed resume review."]
        return "revalidate", "pause", True, ["Paused work needs fresh evidence before resumption."]
    if state in {"funded", "build"}:
        if not item["evidence_fresh"]:
            return "revalidate", state, True, ["Investment evidence is stale."]
        return "continue", state, True, ["Continue only to the current funded milestone."]
    if state == "opportunity" and item["founder_charter_status"] == "authorized":
        return "discover", "discovery", True, [
            "An authorized opportunity must enter bounded discovery before funding comparison."
        ]
    if item["founder_charter_status"] != "authorized":
        if (
            item["strategic_alignment"] <= 1
            and item["user_evidence"] <= 1
            and item["option_value"] <= 1
        ):
            return "reject", "retire", True, ["Weak strategic, user, and option-value evidence does not justify discovery."]
        return "discover", "discovery", True, ["Founder intent is not authorized; only reversible discovery may proceed."]
    if item["user_evidence"] < 2 and item["option_value"] < 4:
        return "discover", "discovery", True, ["Evidence is too weak for investment; run the next reversible evidence action."]
    return "fund-candidate", "funded", False, ["The item is eligible for bounded portfolio comparison."]


def plan(data: dict[str, Any]) -> dict[str, Any]:
    studio_id = non_empty_string(data.get("studio_id"), "studio_id")
    if data.get("company_policy_version") != COMPANY_POLICY_VERSION:
        fail(f"company_policy_version must be {COMPANY_POLICY_VERSION}")
    as_of = iso_date(data.get("as_of"), "as_of")
    active_limit = bounded_int(
        data.get("portfolio_active_limit", 1), "portfolio_active_limit", 0, 256
    )
    total_envelope = envelope(data.get("investment_envelope"), "investment_envelope")
    reserved = envelope(data.get("reserved_envelope"), "reserved_envelope")
    for key in ENVELOPE_KEYS:
        if reserved[key] > total_envelope[key]:
            fail(f"reserved_envelope.{key} exceeds investment_envelope.{key}")
    available = {key: total_envelope[key] - reserved[key] for key in ENVELOPE_KEYS}

    raw_assets = indexed_objects(
        object_list(data.get("product_assets", []), "product_assets"), "product_assets"
    )
    assets = {
        asset_id: normalize_asset(asset_id, raw) for asset_id, raw in raw_assets.items()
    }
    raw_evidence = indexed_objects(
        object_list(data.get("reality_evidence", []), "reality_evidence"), "reality_evidence"
    )
    evidence = {
        evidence_id: normalize_reality_evidence(evidence_id, raw)
        for evidence_id, raw in raw_evidence.items()
    }
    raw_capabilities = indexed_objects(
        object_list(data.get("capabilities", []), "capabilities"), "capabilities"
    )
    for capability_id, raw in raw_capabilities.items():
        validate_capability(capability_id, raw)
    object_list(data.get("decision_history", []), "decision_history")

    raw_items = indexed_objects(
        object_list(data.get("portfolio_items", []), "portfolio_items"), "portfolio_items"
    )
    items = [normalize_item(item_id, raw, assets) for item_id, raw in raw_items.items()]
    for item in items:
        missing_evidence = sorted(set(item["reality_evidence_refs"]) - set(raw_evidence))
        if missing_evidence:
            fail(f"{item['id']} references missing reality evidence: {', '.join(missing_evidence)}")
        referenced_evidence = [evidence[evidence_id] for evidence_id in item["reality_evidence_refs"]]
        derived_freshness = any(
            record["observed_at"] <= as_of <= record["fresh_until"]
            for record in referenced_evidence
        )
        if item["evidence_fresh"] != derived_freshness:
            fail(
                f"{item['id']}.evidence_fresh conflicts with evidence dates as of {as_of.isoformat()}"
            )
        item["has_qualifying_external_outcome"] = any(
            record["evidence_class"] in {"external-outcome", "production-observation"}
            and not record["producer_controls_source"]
            and record["observed_at"] <= as_of <= record["fresh_until"]
            and record["confidence"] >= 3
            for record in referenced_evidence
        )
        if item["current_state"] == "scale" and not item["has_qualifying_external_outcome"]:
            fail(
                f"{item['id']} cannot scale without fresh non-producer-controlled outcome evidence"
            )
        if item["asset_id"]:
            asset = assets[item["asset_id"]]
            if item["current_state"] in {"operate", "scale"} and asset["lifecycle_state"] not in {"operate", "scale"}:
                fail(f"{item['id']} state conflicts with product asset lifecycle_state")
            if item["current_state"] == "scale" and not asset["evidence_fresh"]:
                fail(f"{item['id']} cannot scale with stale product asset evidence")

    active_count = sum(item["current_state"] in ACTIVE_INVESTMENT_STATES for item in items)
    free_slots = max(0, active_limit - active_count)
    decisions: list[dict[str, Any]] = []
    candidates: list[tuple[int, dict[str, Any], str, str, list[str]]] = []

    for item in items:
        action, next_state, fixed, reasons = base_decision(item)
        score = priority_score(item)
        if fixed:
            decisions.append(
                {
                    "id": item["id"],
                    "current_state": item["current_state"],
                    "recommended_action": action,
                    "recommended_next_state": next_state,
                    "priority_score": score,
                    "hard_gate_or_obligation": True,
                    "reasons": reasons,
                    "next_evidence_action": item["next_evidence_action"],
                }
            )
        else:
            candidates.append((score, item, action, next_state, reasons))

    candidates.sort(key=lambda value: (-value[0], value[1]["id"]))
    selected: list[str] = []
    queued: list[str] = []
    used = {key: 0 for key in ENVELOPE_KEYS}
    for score, item, action, next_state, reasons in candidates:
        costs = {key: item[key] for key in ENVELOPE_KEYS}
        fits_budget = all(used[key] + costs[key] <= available[key] for key in ENVELOPE_KEYS)
        if score <= 0:
            final_action = "discover" if item["current_state"] != "operate" else "continue"
            final_state = "discovery" if final_action == "discover" else "operate"
            reasons = reasons + ["Estimated marginal organizational value does not justify this investment horizon."]
        elif free_slots <= 0 or not fits_budget:
            final_action = "queue"
            final_state = item["current_state"]
            queued.append(item["id"])
            reasons = reasons + ["The active-project limit or available investment envelope is binding."]
        else:
            final_action = "fund" if action == "fund-candidate" else "scale"
            final_state = next_state
            free_slots -= 1
            for key in ENVELOPE_KEYS:
                used[key] += costs[key]
            selected.append(item["id"])
        decisions.append(
            {
                "id": item["id"],
                "current_state": item["current_state"],
                "recommended_action": final_action,
                "recommended_next_state": final_state,
                "priority_score": score,
                "hard_gate_or_obligation": False,
                "reasons": reasons,
                "next_evidence_action": item["next_evidence_action"],
            }
        )

    decisions.sort(key=lambda decision: decision["id"])
    for decision in decisions:
        current_state = decision["current_state"]
        next_state = decision["recommended_next_state"]
        if next_state not in ALLOWED_TRANSITIONS[current_state]:
            fail(
                f"planner produced illegal transition for {decision['id']}: "
                f"{current_state} -> {next_state}"
            )
    return {
        "valid": True,
        "machine_selected": True,
        "studio_id": studio_id,
        "company_policy_version": COMPANY_POLICY_VERSION,
        "planner_version": PLANNER_VERSION,
        "transition_closed": True,
        "estimate_not_measured": True,
        "portfolio_active_limit": active_limit,
        "current_active_investments": active_count,
        "available_envelope": available,
        "selected_incremental_envelope": used,
        "selected_new_investments": selected,
        "queued_investments": queued,
        "recommendations": decisions,
        "control_note": (
            "Recommendations do not bypass Founder, human, permission, runtime, release, or external-effect gates. "
            "Record the accountable decision and update persistent studio state after approval."
        ),
    }


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail("studio state must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="STUDIO_STATE.json or compatible snapshot")
    args = parser.parse_args()
    try:
        result = plan(load(args.input))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
