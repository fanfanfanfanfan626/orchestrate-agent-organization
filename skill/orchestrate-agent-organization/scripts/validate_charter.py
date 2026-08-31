#!/usr/bin/env python3
"""Validate child-agent authority, budget, depth, lease, and separation rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BUDGET_KEYS = ("token_units", "cash", "compute_units")
TOKEN_TIERS = {"low", "medium", "high", "very-high"}
LEARNING_AUTHORITIES = {"none", "propose", "commit-approved"}
COMPANY_POLICY_VERSION = "company-v5"
AUTHORITATIVE_RUNTIME_SOURCE = "collaboration.list_agents"
WRITE_SCOPE_MODES = {"read-only", "isolated-worktree"}
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
REQUIRED_CHILD_FIELDS = (
    "id",
    "parent_id",
    "mission",
    "deliverables",
    "success_criteria",
    "company_policy_version",
    "lifecycle_stage",
    "cognitive_mode",
    "context_budget_units",
    "artifact_budget_units",
    "context_sources",
    "learning_authority",
    "token_tier",
    "permissions",
    "delegable_permissions",
    "budget",
    "spawn_quota",
    "current_depth",
    "max_depth",
    "ttl_minutes",
    "auditor_id",
    "auditor_independence",
    "write_scope_mode",
    "write_scope",
    "workspace_id",
    "stop_conditions",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def numeric_budget(value: Any, label: str, errors: list[str]) -> dict[str, float]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {key: 0 for key in BUDGET_KEYS}
    result: dict[str, float] = {}
    for key in BUDGET_KEYS:
        item = value.get(key, 0)
        if isinstance(item, bool) or not isinstance(item, (int, float)) or item < 0:
            errors.append(f"{label}.{key} must be a non-negative number")
            result[key] = 0
        else:
            result[key] = float(item)
    return result


def string_set(value: Any, label: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{label} must be an array of non-empty strings")
        return set()
    normalized = [item.strip() for item in value]
    if len(set(normalized)) != len(normalized):
        errors.append(f"{label} must not contain duplicates")
    return set(normalized)


def repository_scope_set(value: Any, label: str, errors: list[str]) -> set[str]:
    scopes = string_set(value, label, errors)
    valid: set[str] = set()
    for scope in scopes:
        normalized = scope.strip().replace("\\", "/").strip("/")
        parts = normalized.split("/") if normalized else []
        if (
            not normalized
            or scope.startswith(("/", "\\"))
            or ":" in parts[0]
            or any(part in {"", ".", ".."} for part in parts)
        ):
            errors.append(f"{label} entries must be repository-relative normalized paths")
            continue
        valid.add(normalized)
    return valid


def scopes_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def non_empty_string(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value


def non_negative_int(value: Any, label: str, errors: list[str]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{label} must be a non-negative integer")
        return 0
    return value


def validate(parent: dict[str, Any], child: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [field for field in REQUIRED_CHILD_FIELDS if field not in child]
    if missing:
        errors.append("child is missing required fields: " + ", ".join(missing))

    parent_id = non_empty_string(parent.get("id"), "parent.id", errors)
    child_id = non_empty_string(child.get("id"), "child.id", errors)
    non_empty_string(child.get("mission"), "child.mission", errors)
    if child.get("parent_id") != parent_id:
        errors.append("child.parent_id must equal parent.id")
    if child_id == parent_id:
        errors.append("child.id must differ from parent.id")

    runtime_source = non_empty_string(
        parent.get("runtime_snapshot_source"), "parent.runtime_snapshot_source", errors
    )
    if runtime_source and runtime_source != AUTHORITATIVE_RUNTIME_SOURCE:
        errors.append(
            f"parent.runtime_snapshot_source must be {AUTHORITATIVE_RUNTIME_SOURCE}"
        )
    active_agents = string_set(
        parent.get("runtime_active_agents"), "parent.runtime_active_agents", errors
    )
    if parent_id and parent_id not in active_agents:
        errors.append("parent.runtime_active_agents must contain parent.id")
    authorized_auditors = string_set(
        parent.get("authorized_auditor_ids"), "parent.authorized_auditor_ids", errors
    )
    inactive_auditors = sorted(authorized_auditors - active_agents)
    if inactive_auditors:
        errors.append(
            "parent.authorized_auditor_ids contains inactive ids: "
            + ", ".join(inactive_auditors)
        )

    parent_policy = parent.get("company_policy_version")
    child_policy = child.get("company_policy_version")
    if parent_policy != COMPANY_POLICY_VERSION:
        errors.append(f"parent.company_policy_version must be {COMPANY_POLICY_VERSION}")
    if child_policy != COMPANY_POLICY_VERSION:
        errors.append(f"child.company_policy_version must be {COMPANY_POLICY_VERSION}")
    elif child_policy != parent_policy:
        errors.append("child.company_policy_version must equal parent.company_policy_version")

    if child.get("lifecycle_stage") not in LIFECYCLE_STAGES:
        errors.append("child.lifecycle_stage is not allowed")
    if child.get("cognitive_mode") not in COGNITIVE_MODES:
        errors.append("child.cognitive_mode is not allowed")

    context_budget = child.get("context_budget_units")
    if (
        isinstance(context_budget, bool)
        or not isinstance(context_budget, int)
        or not 1 <= context_budget <= 8
    ):
        errors.append("child.context_budget_units must be an integer from 1 to 8")
    artifact_budget = child.get("artifact_budget_units")
    if (
        isinstance(artifact_budget, bool)
        or not isinstance(artifact_budget, int)
        or not 1 <= artifact_budget <= 8
    ):
        errors.append("child.artifact_budget_units must be an integer from 1 to 8")
    context_sources = string_set(
        child.get("context_sources"), "child.context_sources", errors
    )
    if not context_sources:
        errors.append("child.context_sources must contain at least one scoped source")
    learning_authority = child.get("learning_authority")
    if learning_authority not in LEARNING_AUTHORITIES:
        errors.append("child.learning_authority must be none, propose, or commit-approved")

    child_token_tier = child.get("token_tier")
    if child_token_tier not in TOKEN_TIERS:
        errors.append("child.token_tier must be low, medium, high, or very-high")

    parent_delegable = string_set(parent.get("delegable_permissions", []), "parent.delegable_permissions", errors)
    child_permissions = string_set(child.get("permissions", []), "child.permissions", errors)
    child_delegable = string_set(child.get("delegable_permissions", []), "child.delegable_permissions", errors)
    excess_permissions = sorted(child_permissions - parent_delegable)
    if excess_permissions:
        errors.append("child permissions exceed parent delegation: " + ", ".join(excess_permissions))
    excess_delegable = sorted(child_delegable - child_permissions)
    if excess_delegable:
        errors.append("child delegates permissions it does not hold: " + ", ".join(excess_delegable))
    if learning_authority == "commit-approved" and "memory:write-approved" not in child_permissions:
        errors.append(
            "child.learning_authority commit-approved requires memory:write-approved permission"
        )

    write_scope_mode = child.get("write_scope_mode")
    if write_scope_mode not in WRITE_SCOPE_MODES:
        errors.append("child.write_scope_mode must be read-only or isolated-worktree")
    write_scopes = repository_scope_set(
        child.get("write_scope"), "child.write_scope", errors
    )
    workspace_id = non_empty_string(
        child.get("workspace_id"), "child.workspace_id", errors
    )
    authorized_workspaces = string_set(
        parent.get("authorized_workspace_ids"), "parent.authorized_workspace_ids", errors
    )
    reserved_workspaces = string_set(
        parent.get("reserved_workspace_ids", []), "parent.reserved_workspace_ids", errors
    )
    reserved_scopes = repository_scope_set(
        parent.get("reserved_write_scopes", []), "parent.reserved_write_scopes", errors
    )
    workspace_write = any(
        permission.endswith(":write") and not permission.startswith("memory:")
        for permission in child_permissions
    )
    if workspace_write:
        if write_scope_mode != "isolated-worktree":
            errors.append("write-capable child requires isolated-worktree write_scope_mode")
        if not write_scopes:
            errors.append("write-capable child requires at least one write_scope")
        if workspace_id == "none":
            errors.append("write-capable child requires a runtime-issued workspace_id")
        if workspace_id and workspace_id not in authorized_workspaces:
            errors.append("child.workspace_id is not authorized by the parent runtime roster")
        if workspace_id in reserved_workspaces:
            errors.append("child.workspace_id is already reserved")
        for scope in write_scopes:
            if any(scopes_overlap(scope, reserved) for reserved in reserved_scopes):
                errors.append(f"child.write_scope overlaps a reserved scope: {scope}")
    else:
        if write_scope_mode != "read-only":
            errors.append("non-writing child must use read-only write_scope_mode")
        if write_scopes:
            errors.append("non-writing child must have an empty write_scope")
        if workspace_id and workspace_id != "none":
            errors.append("non-writing child.workspace_id must be none")

    parent_budget = numeric_budget(parent.get("budget", {}), "parent.budget", errors)
    reserved_budget = numeric_budget(
        parent.get("reserved_budget", {}), "parent.reserved_budget", errors
    )
    child_budget = numeric_budget(child.get("budget", {}), "child.budget", errors)
    for key in BUDGET_KEYS:
        if reserved_budget[key] > parent_budget[key]:
            errors.append(f"parent.reserved_budget.{key} exceeds parent.budget.{key}")
        if reserved_budget[key] + child_budget[key] > parent_budget[key]:
            errors.append(
                f"reserved plus child budget for {key} exceeds parent.budget.{key}"
            )

    parent_quota = non_negative_int(parent.get("spawn_quota", 0), "parent.spawn_quota", errors)
    reserved_spawn_units = non_negative_int(
        parent.get("reserved_spawn_units", 0), "parent.reserved_spawn_units", errors
    )
    child_quota = non_negative_int(child.get("spawn_quota", 0), "child.spawn_quota", errors)
    if reserved_spawn_units + 1 + child_quota > parent_quota:
        errors.append("child and descendant reservations exceed parent.spawn_quota")

    parent_depth = non_negative_int(parent.get("current_depth", 0), "parent.current_depth", errors)
    child_depth = non_negative_int(child.get("current_depth", 0), "child.current_depth", errors)
    parent_max_depth = non_negative_int(parent.get("max_depth", 0), "parent.max_depth", errors)
    child_max_depth = non_negative_int(child.get("max_depth", 0), "child.max_depth", errors)
    if child_depth != parent_depth + 1:
        errors.append("child.current_depth must equal parent.current_depth + 1")
    if child_depth > parent_max_depth:
        errors.append("child depth exceeds parent.max_depth")
    if parent_depth > parent_max_depth:
        errors.append("parent.current_depth exceeds parent.max_depth")
    if child_depth > child_max_depth:
        errors.append("child.current_depth exceeds child.max_depth")
    if child_max_depth > parent_max_depth:
        errors.append("child.max_depth exceeds parent.max_depth")
    if child_quota > 0 and child_depth >= child_max_depth:
        errors.append("positive child.spawn_quota requires remaining descendant depth")

    parent_ttl = non_negative_int(parent.get("ttl_minutes", 0), "parent.ttl_minutes", errors)
    child_ttl = non_negative_int(child.get("ttl_minutes", 0), "child.ttl_minutes", errors)
    if child_ttl == 0:
        errors.append("child.ttl_minutes must be positive")
    if parent_ttl and child_ttl > parent_ttl:
        errors.append("child.ttl_minutes exceeds parent lease")

    auditor_id = non_empty_string(child.get("auditor_id"), "child.auditor_id", errors)
    if auditor_id and auditor_id == child_id:
        errors.append("a child cannot be its own auditor")
    if auditor_id and auditor_id not in authorized_auditors:
        errors.append("child.auditor_id is not an authorized active auditor")
    auditor_independence = child.get("auditor_independence")
    if auditor_independence not in {"parent-accountable", "independent-assurance"}:
        errors.append(
            "child.auditor_independence must be parent-accountable or independent-assurance"
        )
    elif auditor_independence == "parent-accountable" and auditor_id != parent_id:
        errors.append("parent-accountable auditor must equal parent.id")
    elif auditor_independence == "independent-assurance" and auditor_id == parent_id:
        errors.append("independent-assurance auditor must differ from parent.id")

    for field in ("deliverables", "success_criteria", "stop_conditions"):
        value = string_set(child.get(field), f"child.{field}", errors)
        if not value:
            errors.append(f"child.{field} must be a non-empty array")

    if child_quota > 0 and not child_delegable:
        warnings.append("child can spawn descendants but has no delegable permissions")
    if child_budget["token_units"] == 0:
        warnings.append("child token allocation is zero; the control plane should replan")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--child", type=Path, required=True)
    args = parser.parse_args()
    try:
        errors, warnings = validate(load_json(args.parent), load_json(args.child))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)], "warnings": []}, ensure_ascii=False, indent=2))
        return 2

    print(
        json.dumps(
            {"valid": not errors, "errors": errors, "warnings": warnings},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
