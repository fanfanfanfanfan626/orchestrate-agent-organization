#!/usr/bin/env python3
"""Automatically size an agent organization from task and runtime state."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


TOKEN_TIERS = ((12, "low"), (30, "medium"), (60, "high"))
TOKEN_MODEL_VERSION = "organizational-fitness-v2"
COMPANY_POLICY_VERSION = "company-v5"
AUTHORITATIVE_RUNTIME_SOURCES = {"collaboration.list_agents"}
FOUNDER_CHARTER_STATUSES = {
    "not-required", "raw", "framed", "explored", "decision-ready", "authorized",
}
PRE_AUTHORIZATION_STAGES = {"control", "discovery", "design", "verify"}
LIFECYCLE_STAGES = {
    "control", "discovery", "design", "build", "integrate", "verify",
    "release", "operate", "maintain", "debug", "evolve", "retire",
}
COGNITIVE_MODES = {
    "organizational-control", "portfolio-stewardship", "founder-partner", "product-discovery", "reuse-first-research",
    "architecture-first-principles", "implementation", "adversarial-review",
    "test-and-falsify", "debug-and-incident", "maintenance-stewardship",
    "security-abuse", "operations-reliability", "integration-release",
}
DEFAULT_MODE_BY_STAGE = {
    "control": "organizational-control",
    "discovery": "product-discovery",
    "design": "architecture-first-principles",
    "build": "implementation",
    "integrate": "integration-release",
    "verify": "test-and-falsify",
    "release": "integration-release",
    "operate": "operations-reliability",
    "maintain": "maintenance-stewardship",
    "debug": "debug-and-incident",
    "evolve": "maintenance-stewardship",
    "retire": "maintenance-stewardship",
}


def fail(message: str) -> None:
    raise ValueError(message)


def bounded_int(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(f"{name} must be an integer")
    if not low <= value <= high:
        fail(f"{name} must be between {low} and {high}")
    return value


def strict_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{name} must be a boolean")
    return value


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("capacity input must be a JSON object")
    return data


def runtime_snapshot(data: dict[str, Any]) -> tuple[int, list[str], bool, str]:
    """Derive active occupancy from names when authoritative telemetry is available."""
    raw_agents = data.get("runtime_active_agents")
    source = data.get("runtime_snapshot_source", "unspecified")
    if not isinstance(source, str) or not source.strip():
        fail("runtime_snapshot_source must be a non-empty string")
    if source not in AUTHORITATIVE_RUNTIME_SOURCES | {"unspecified"}:
        fail("runtime_snapshot_source is not allowed")

    if raw_agents is not None:
        if (
            not isinstance(raw_agents, list)
            or not raw_agents
            or any(not isinstance(agent, str) or not agent.strip() for agent in raw_agents)
        ):
            fail("runtime_active_agents must be a non-empty array of agent names")
        agents = list(dict.fromkeys(agent.strip() for agent in raw_agents))
        if len(agents) != len(raw_agents):
            fail("runtime_active_agents must not contain duplicates")
        active_now = len(agents)
        supplied_now = data.get("runtime_active_now")
        if supplied_now is not None:
            supplied_now = bounded_int(
                supplied_now, "runtime_active_now", 1, 256
            )
            if supplied_now != active_now:
                fail("runtime_active_now conflicts with runtime_active_agents")
        if source not in AUTHORITATIVE_RUNTIME_SOURCES:
            fail(
                "runtime_snapshot_source is not an allowed authoritative source; "
                "runtime_active_agents requires collaboration.list_agents"
            )
        return active_now, agents, True, source

    if source != "unspecified":
        fail("runtime_active_agents is required for an authoritative runtime source")
    active_now = bounded_int(
        data.get("runtime_active_now", 1), "runtime_active_now", 1, 256
    )
    return active_now, [], False, source


def token_tier(effort: float) -> str:
    for ceiling, tier in TOKEN_TIERS:
        if effort <= ceiling:
            return tier
    return "very-high"


def normalize_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        fail("items must be a non-empty array")

    normalized = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"items[{index}] must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            fail(f"items[{index}].id must be a non-empty string")
        item_id = item_id.strip()
        if item_id in seen_ids:
            fail(f"duplicate item id: {item_id}")
        seen_ids.add(item_id)

        complexity = bounded_int(item.get("complexity", 1), f"{item_id}.complexity", 1, 5)
        risk = bounded_int(item.get("risk", 0), f"{item_id}.risk", 0, 4)
        estimated_units = bounded_int(
            item.get("estimated_units", 1), f"{item_id}.estimated_units", 1, 8
        )
        context_units = bounded_int(
            item.get("context_units", complexity), f"{item_id}.context_units", 1, 5
        )
        parallelizable = strict_bool(
            item.get("parallelizable", False), f"{item_id}.parallelizable"
        )
        independent = strict_bool(
            item.get("independent", False), f"{item_id}.independent"
        )
        coupling = bounded_int(
            item.get("coupling", 1 if parallelizable and independent else 4),
            f"{item_id}.coupling",
            0,
            4,
        )
        context_isolation = bounded_int(
            item.get("context_isolation", max(0, context_units - 2) if independent else 0),
            f"{item_id}.context_isolation",
            0,
            4,
        )
        specialist_need = bounded_int(
            item.get("specialist_need", 0), f"{item_id}.specialist_need", 0, 4
        )
        critical_path = bounded_int(
            item.get("critical_path", 1 if parallelizable else 0),
            f"{item_id}.critical_path",
            0,
            4,
        )
        requires_separation_of_duties = strict_bool(
            item.get("requires_separation_of_duties", False),
            f"{item_id}.requires_separation_of_duties",
        )
        lifecycle_stage = item.get("lifecycle_stage", "design")
        if lifecycle_stage not in LIFECYCLE_STAGES:
            fail(f"{item_id}.lifecycle_stage is not allowed")
        cognitive_mode = item.get(
            "cognitive_mode", DEFAULT_MODE_BY_STAGE[lifecycle_stage]
        )
        if cognitive_mode not in COGNITIVE_MODES:
            fail(f"{item_id}.cognitive_mode is not allowed")
        effort = complexity * estimated_units + context_units + 2 * risk
        focus_rate_points = min(
            30,
            4 * (complexity - 1)
            + 3 * (context_units - 1)
            + (3 if independent else 0),
        )
        focus_savings = max(0, round(effort * focus_rate_points / 100))
        context_packet_overhead = 1 + math.ceil(context_units / 2) + coupling
        integration_overhead = 2 + coupling
        net_delegation_savings = (
            focus_savings - context_packet_overhead - integration_overhead
        )
        quality_gain = (
            2 * context_isolation
            + 2 * specialist_need
            + 2 * max(0, complexity - 3)
        )
        critical_path_gain = critical_path * max(1, math.ceil(estimated_units / 3))
        control_gain = 10 if requires_separation_of_duties else 0
        organization_value = (
            net_delegation_savings
            + quality_gain
            + critical_path_gain
            + control_gain
        )
        selection_drivers = []
        if net_delegation_savings > 0:
            selection_drivers.append("token-efficiency")
        if context_isolation > 0:
            selection_drivers.append("context-isolation")
        if specialist_need > 0:
            selection_drivers.append("specialist-capability")
        if critical_path > 0:
            selection_drivers.append("critical-path-latency")
        if requires_separation_of_duties:
            selection_drivers.append("separation-of-duties")
        normalized.append(
            {
                "id": item_id,
                "complexity": complexity,
                "risk": risk,
                "estimated_units": estimated_units,
                "context_units": context_units,
                "parallelizable": parallelizable,
                "independent": independent,
                "coupling": coupling,
                "context_isolation": context_isolation,
                "specialist_need": specialist_need,
                "critical_path": critical_path,
                "requires_separation_of_duties": requires_separation_of_duties,
                "lifecycle_stage": lifecycle_stage,
                "cognitive_mode": cognitive_mode,
                "requires_independent_verification": strict_bool(
                    item.get("requires_independent_verification", False),
                    f"{item_id}.requires_independent_verification",
                ),
                "effort": effort,
                "focus_savings": focus_savings,
                "context_packet_overhead": context_packet_overhead,
                "integration_overhead": integration_overhead,
                "net_delegation_savings": net_delegation_savings,
                "quality_gain": quality_gain,
                "critical_path_gain": critical_path_gain,
                "control_gain": control_gain,
                "organization_value": organization_value,
                "selection_drivers": selection_drivers,
            }
        )
    return normalized


def allocate_token_weights(allocations: list[dict[str, Any]]) -> None:
    total = sum(allocation["token_weight"] for allocation in allocations)
    remaining = 100
    for index, allocation in enumerate(allocations):
        if index == len(allocations) - 1:
            share = remaining
        else:
            share = max(1, round(allocation["token_weight"] * 100 / total))
            share = min(share, remaining - (len(allocations) - index - 1))
        allocation["token_share_percent"] = share
        allocation["token_tier"] = token_tier(allocation["token_weight"])
        remaining -= share


def plan_capacity(data: dict[str, Any]) -> dict[str, Any]:
    active_limit = bounded_int(
        data.get("runtime_active_limit", 1), "runtime_active_limit", 1, 256
    )
    active_now, active_agents, snapshot_authoritative, snapshot_source = runtime_snapshot(data)
    if active_now > active_limit:
        fail("active runtime occupancy exceeds runtime_active_limit")
    decision_level = bounded_int(data.get("decision_level", 1), "decision_level", 0, 5)
    company_policy_version = data.get("company_policy_version", COMPANY_POLICY_VERSION)
    if company_policy_version != COMPANY_POLICY_VERSION:
        fail(f"company_policy_version must be {COMPANY_POLICY_VERSION}")
    mandatory_human_gate = strict_bool(
        data.get("mandatory_human_gate", False), "mandatory_human_gate"
    )
    founder_discovery_required = strict_bool(
        data.get("founder_discovery_required", False), "founder_discovery_required"
    )
    founder_charter_status = data.get(
        "founder_charter_status", "raw" if founder_discovery_required else "not-required"
    )
    if founder_charter_status not in FOUNDER_CHARTER_STATUSES:
        fail("founder_charter_status is not allowed")
    if founder_discovery_required and founder_charter_status == "not-required":
        fail("founder_charter_status cannot be not-required when discovery is required")
    if not founder_discovery_required and founder_charter_status != "not-required":
        fail("founder_charter_status must be not-required when discovery is not required")
    founder_authorized = (
        not founder_discovery_required or founder_charter_status == "authorized"
    )
    physical_free_child_slots = max(0, active_limit - active_now)
    free_child_slots = (
        physical_free_child_slots
        if snapshot_authoritative
        else min(1, physical_free_child_slots)
    )
    items = normalize_items(data.get("items", []))
    if not founder_authorized:
        disallowed = sorted(
            item["id"] for item in items
            if item["lifecycle_stage"] not in PRE_AUTHORIZATION_STAGES
        )
        if disallowed:
            fail(
                "pre-authorization capacity input contains implementation stages: "
                + ", ".join(disallowed)
            )

    potential_candidates = [
        item
        for item in items
        if item["parallelizable"]
        and item["independent"]
        and item["effort"] >= 6
    ]
    token_efficient_candidates = [
        item for item in potential_candidates if item["net_delegation_savings"] > 0
    ]
    candidates = [item for item in potential_candidates if item["organization_value"] > 0]
    candidates.sort(
        key=lambda item: (
            -item["organization_value"],
            -item["effort"],
            -item["risk"],
            item["id"],
        )
    )

    material_risk = any(
        item["risk"] >= 3 or item["requires_independent_verification"] for item in items
    )
    parallel_effort = sum(item["effort"] for item in candidates)
    total_effort = sum(item["effort"] for item in items) + max(0, len(items) - 1) * 2

    expected_rework_units = math.ceil(
        sum(
            item["risk"]
            * (item["complexity"] + item["estimated_units"] + item["context_units"])
            / 4
            + (4 if item["requires_independent_verification"] else 0)
            for item in items
        )
    )
    verification_weight = max(
        6,
        sum(
            2 * (item["risk"] + 1)
            for item in items
            if item["risk"] >= 3 or item["requires_independent_verification"]
        ),
    )
    expected_rework_avoidance = (
        round(expected_rework_units * 0.70) if material_risk else 0
    )
    verifier_required = any(
        item["requires_independent_verification"] for item in items
    ) or (decision_level >= 2 and material_risk)
    verifier_token_efficient = expected_rework_avoidance >= verification_weight

    verifier_count = (
        1
        if material_risk
        and free_child_slots > 0
        and (verifier_required or verifier_token_efficient)
        else 0
    )
    worker_capacity = max(0, free_child_slots - verifier_count)
    orchestration_only_lead = parallel_effort >= 30 or len(candidates) >= 4

    desired_workers = 0
    if len(candidates) >= 2:
        desired_workers = len(candidates) if orchestration_only_lead else len(candidates) - 1
    elif len(candidates) == 1 and len(items) >= 2:
        desired_workers = 1
    worker_count = min(worker_capacity, desired_workers)

    if mandatory_human_gate:
        worker_count = 0
        verifier_count = 0

    delegated = candidates[:worker_count]
    delegated_ids = {item["id"] for item in delegated}
    lead_items = [item for item in items if item["id"] not in delegated_ids]
    recommended_children = worker_count + verifier_count

    decomposition_difficulty_savings = sum(
        item["focus_savings"] for item in delegated
    )
    context_packet_overhead = sum(
        item["context_packet_overhead"] for item in delegated
    )
    integration_overhead = sum(item["integration_overhead"] for item in delegated)
    applied_rework_avoidance = expected_rework_avoidance if verifier_count else 0
    applied_verification_weight = verification_weight if verifier_count else 0
    single_agent_expected_token_units = total_effort + expected_rework_units
    selected_plan_expected_token_units = max(
        1,
        single_agent_expected_token_units
        - decomposition_difficulty_savings
        + context_packet_overhead
        + integration_overhead
        + applied_verification_weight
        - applied_rework_avoidance,
    )
    estimated_token_savings_units = (
        single_agent_expected_token_units - selected_plan_expected_token_units
    )
    estimated_token_savings_percent = round(
        estimated_token_savings_units * 100 / single_agent_expected_token_units,
        1,
    )
    selected_quality_gain = sum(item["quality_gain"] for item in delegated)
    selected_critical_path_gain = sum(
        item["critical_path_gain"] for item in delegated
    )
    selected_control_gain = sum(item["control_gain"] for item in delegated)
    selected_organization_value_units = (
        estimated_token_savings_units
        + selected_quality_gain
        + selected_critical_path_gain
        + selected_control_gain
    )

    reasons: list[str] = []
    if not snapshot_authoritative:
        reasons.append("Runtime occupancy is non-authoritative; creation is conservatively capped at one child.")
    if mandatory_human_gate:
        reasons.append("A mandatory human gate is open; no child may be activated before it is resolved.")
    elif not founder_authorized:
        reasons.append(
            "The Founder Charter is not authorized; only reversible discovery, design, and assurance work may proceed."
        )
    elif free_child_slots == 0:
        reasons.append("Runtime has no free child slot; the lead must execute and verify serially.")
    elif not potential_candidates:
        reasons.append("No substantive independent workstream is available for focused delegation.")
    elif not candidates:
        reasons.append(
            "Independent work exists, but its token, quality, latency, specialist, and control benefits do not exceed coordination cost."
        )
    elif worker_count:
        execution_token_delta = (
            decomposition_difficulty_savings
            - context_packet_overhead
            - integration_overhead
        )
        driver_names = sorted(
            {driver for item in delegated for driver in item["selection_drivers"]}
        )
        reasons.append(
            f"{len(candidates)} organizationally valuable workstreams justify {worker_count} worker child"
            + ("ren" if worker_count != 1 else "")
            + f" for {', '.join(driver_names)}; net execution token delta (positive means savings) is {execution_token_delta} units before assurance."
        )
    if material_risk and verifier_count:
        assurance_delta = applied_rework_avoidance - applied_verification_weight
        if assurance_delta >= 0:
            reasons.append(
                f"Independent assurance is estimated to avoid {applied_rework_avoidance} rework units at a cost of {applied_verification_weight}, saving {assurance_delta} token units while separating duties."
            )
        else:
            reasons.append(
                f"Independent assurance adds an estimated {-assurance_delta}-unit safety premium; material D{decision_level} risk requires the separation of duties."
            )
    elif material_risk and not mandatory_human_gate:
        if free_child_slots == 0:
            reasons.append("Material risk exists, but verification must run serially because capacity is full.")
        else:
            reasons.append(
                "Material risk exists, but a separate verifier is neither mandated at this decision level nor estimated to reduce total tokens; apply serial challenge."
            )
    if worker_count < desired_workers and not mandatory_human_gate:
        reasons.append(
            "One or more parallel workstreams remain with the lead or queue because runtime concurrency is the binding limit."
        )

    allocations: list[dict[str, Any]] = []
    lead_weight = max(
        4,
        sum(item["effort"] for item in lead_items) + integration_overhead,
    )
    founder_pending = founder_discovery_required and not founder_authorized
    allocations.append(
        {
            "agent": "lead",
            "role": (
                "Founder Partner: human dialogue, synthesis, and authorization preparation"
                if founder_pending
                else "control, integration, and queued execution"
            ),
            "workstreams": [item["id"] for item in lead_items],
            "token_weight": lead_weight,
            "company_policy_version": company_policy_version,
            "lifecycle_stage": "discovery" if founder_pending else "control",
            "cognitive_mode": "founder-partner" if founder_pending else "organizational-control",
            "context_budget_units": 5,
            "artifact_budget_units": min(8, max(2, len(lead_items) + 2)),
            "context_source_policy": "project map plus only sources needed for control and integration",
            "learning_authority": "commit-approved",
        }
    )

    for index, item in enumerate(delegated, start=1):
        allocations.append(
            {
                "agent": f"worker-{index}",
                "role": "bounded mission worker",
                "workstreams": [item["id"]],
                "token_weight": max(
                    4,
                    item["effort"]
                    - item["focus_savings"]
                    + item["context_packet_overhead"],
                ),
                "estimated_focus_savings": item["focus_savings"],
                "context_packet_overhead": item["context_packet_overhead"],
                "interface_coupling": item["coupling"],
                "estimated_organization_value": item["organization_value"],
                "selection_drivers": item["selection_drivers"],
                "company_policy_version": company_policy_version,
                "lifecycle_stage": item["lifecycle_stage"],
                "cognitive_mode": item["cognitive_mode"],
                "context_budget_units": item["context_units"],
                "artifact_budget_units": 2,
                "context_source_policy": "project map node plus scoped source, interface, test, and evidence paths",
                "learning_authority": "propose",
            }
        )

    if verifier_count:
        allocations.append(
            {
                "agent": "verifier-1",
                "role": "independent assurance",
                "workstreams": [item["id"] for item in items if item["risk"] >= 2],
                "token_weight": verification_weight,
                "company_policy_version": company_policy_version,
                "lifecycle_stage": "verify",
                "cognitive_mode": "adversarial-review",
                "context_budget_units": 4,
                "artifact_budget_units": 1,
                "context_source_policy": "acceptance criteria plus changed interfaces, tests, evidence, and risk paths",
                "learning_authority": "propose",
            }
        )

    allocate_token_weights(allocations)

    direct_eligible = (
        not mandatory_human_gate
        and not founder_pending
        and decision_level <= 1
        and not material_risk
        and total_effort <= 12
        and len(items) <= 2
        and len(candidates) < 2
        and recommended_children == 0
    )
    if mandatory_human_gate:
        execution_route = "human-gated"
    elif founder_pending:
        execution_route = "founder-discovery"
    elif direct_eligible:
        execution_route = "direct"
    elif recommended_children > 0:
        execution_route = "organized"
    else:
        execution_route = "governed-serial"

    if execution_route == "human-gated":
        selected_topology = "human-gated-control-plane"
    elif execution_route == "founder-discovery":
        selected_topology = (
            "founder-office-with-advisory-cells"
            if recommended_children > 0
            else "founder-office"
        )
    elif worker_count and verifier_count:
        selected_topology = "mission-cell-with-independent-assurance"
    elif worker_count:
        selected_topology = "mission-cell"
    elif verifier_count:
        selected_topology = "lead-with-independent-assurance"
    else:
        selected_topology = "lead-only"

    return {
        "machine_selected": True,
        "execution_route": execution_route,
        "selected_topology": selected_topology,
        "load_governance_references": execution_route != "direct",
        "load_organization_references": execution_route != "direct",
        "load_founder_office_reference": founder_discovery_required,
        "decision_level": decision_level,
        "company_policy_version": company_policy_version,
        "mandatory_human_gate": mandatory_human_gate,
        "founder_discovery_required": founder_discovery_required,
        "founder_charter_status": founder_charter_status,
        "implementation_activation_allowed": founder_authorized and not mandatory_human_gate,
        "allowed_pre_authorization_stages": sorted(PRE_AUTHORIZATION_STAGES),
        "selected_organization_token_tier": token_tier(selected_plan_expected_token_units),
        "estimated_effort_points": total_effort,
        "token_model_version": TOKEN_MODEL_VERSION,
        "token_estimate_not_measured": True,
        "single_agent_expected_token_units": single_agent_expected_token_units,
        "selected_plan_expected_token_units": selected_plan_expected_token_units,
        "estimated_token_savings_units": estimated_token_savings_units,
        "estimated_token_savings_percent": estimated_token_savings_percent,
        "selected_quality_gain_units": selected_quality_gain,
        "selected_critical_path_gain_units": selected_critical_path_gain,
        "selected_control_gain_units": selected_control_gain,
        "selected_organization_value_units": selected_organization_value_units,
        "decomposition_difficulty_savings_units": decomposition_difficulty_savings,
        "context_packet_overhead_units": context_packet_overhead,
        "integration_overhead_units": integration_overhead,
        "expected_single_agent_rework_units": expected_rework_units,
        "expected_rework_avoidance_units": applied_rework_avoidance,
        "independent_assurance_cost_units": applied_verification_weight,
        "recommended_children": recommended_children,
        "ceiling_not_target": True,
        "maximum_active_agents_including_existing": active_now + recommended_children,
        "worker_children": worker_count,
        "verifier_children": verifier_count,
        "delegated_workstreams": [item["id"] for item in delegated],
        "lead_or_queued_workstreams": [item["id"] for item in lead_items],
        "eligible_independent_workstreams": len(potential_candidates),
        "token_efficient_delegation_workstreams": len(token_efficient_candidates),
        "organizationally_valuable_workstreams": len(candidates),
        "free_child_slots_observed": free_child_slots,
        "physical_free_child_slots": physical_free_child_slots,
        "runtime_snapshot_authoritative": snapshot_authoritative,
        "runtime_snapshot_source": snapshot_source,
        "runtime_active_agents": active_agents,
        "default_descendant_spawn_quota": 0,
        "replan_descendant_rule": (
            "A mission child may receive spawn quota only after it exposes at least two substantive "
            "independent substreams and the control plane reruns this planner against current runtime state."
        ),
        "agent_allocations": allocations,
        "replan_triggers": [
            "human changes goal or design decision",
            "task graph gains or loses a workstream",
            "child completes, blocks, or duplicates work",
            "assurance discovers material follow-up",
            "runtime capacity changes",
            "coordination overhead exceeds marginal value",
        ],
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="machine-generated JSON task/runtime description")
    args = parser.parse_args()
    try:
        result = plan_capacity(load_plan(args.input))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"valid": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
