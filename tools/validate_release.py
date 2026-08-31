#!/usr/bin/env python3
"""Validate the public skill package without changing it."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "orchestrate-agent-organization"
SKILL_MD = SKILL / "SKILL.md"

REQUIRED_DIRS = ("agents", "assets", "references", "scripts")
REQUIRED_FILES = (
    "agents/openai.yaml",
    "assets/assurance-manifest.template.json",
    "assets/evidence-attestation.template.json",
    "assets/integration-packet.template.json",
    "assets/studio-state.template.json",
    "references/cognitive-modes.md",
    "references/company-constitution.md",
    "references/contracts.md",
    "references/engineering-system.md",
    "references/founder-office.md",
    "references/governance.md",
    "references/integration-gate.md",
    "references/organization-architecture.md",
    "references/studio-kernel.md",
    "scripts/plan_capacity.py",
    "scripts/plan_capacity.ps1",
    "scripts/plan_portfolio.py",
    "scripts/plan_portfolio.ps1",
    "scripts/validate_charter.py",
    "scripts/validate_charter.ps1",
    "scripts/validate_integration.py",
    "scripts/validate_integration.ps1",
)

LOCAL_OR_SECRET_PATTERNS = {
    "Windows user path": re.compile(r"(?i)C:\\Users\\"),
    "macOS user path": re.compile(r"/Users/[^/\s]+/"),
    "GitHub token": re.compile(r"(?:ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)"),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(text: str, errors: list[str]) -> dict[str, object]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        fail(errors, "SKILL.md must begin with YAML frontmatter")
        return {}
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        fail(errors, "SKILL.md frontmatter must be a mapping")
        return {}
    if set(data) != {"name", "description"}:
        fail(errors, "SKILL.md frontmatter must contain only name and description")
    if data.get("name") != "orchestrate-agent-organization":
        fail(errors, "SKILL.md name does not match the package directory")
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        fail(errors, "SKILL.md description must be non-empty")
    return data


def main() -> int:
    errors: list[str] = []

    if not SKILL_MD.is_file():
        print(f"ERROR: missing {SKILL_MD.relative_to(ROOT)}", file=sys.stderr)
        return 1

    for directory in REQUIRED_DIRS:
        if not (SKILL / directory).is_dir():
            fail(errors, f"missing directory: {directory}")
    for relative in REQUIRED_FILES:
        if not (SKILL / relative).is_file():
            fail(errors, f"missing file: {relative}")

    skill_text = SKILL_MD.read_text(encoding="utf-8")
    parse_frontmatter(skill_text, errors)
    if len(skill_text.splitlines()) > 500:
        fail(errors, "SKILL.md exceeds 500 lines; move detail into references")

    metadata_path = SKILL / "agents" / "openai.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    interface = metadata.get("interface", {}) if isinstance(metadata, dict) else {}
    if not isinstance(interface, dict):
        fail(errors, "agents/openai.yaml interface must be a mapping")
    else:
        short_description = interface.get("short_description", "")
        if not isinstance(short_description, str) or not 25 <= len(short_description) <= 64:
            fail(errors, "short_description must contain 25-64 characters")
        default_prompt = interface.get("default_prompt", "")
        if "$orchestrate-agent-organization" not in str(default_prompt):
            fail(errors, "default_prompt must explicitly mention $orchestrate-agent-organization")

    referenced_paths = set(
        re.findall(r"(?:references|assets|scripts)/[A-Za-z0-9_.-]+", skill_text)
    )
    for relative in sorted(referenced_paths):
        if not (SKILL / relative).is_file():
            fail(errors, f"SKILL.md references a missing file: {relative}")

    for path in SKILL.rglob("*"):
        relative = path.relative_to(SKILL)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            fail(errors, f"generated file must not ship: {relative}")
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for label, pattern in LOCAL_OR_SECRET_PATTERNS.items():
                if pattern.search(text):
                    fail(errors, f"{label} found in {relative}")

    for template in sorted((SKILL / "assets").glob("*.json")):
        try:
            json.loads(template.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"invalid JSON in {template.relative_to(SKILL)}: {exc}")

    for script in sorted((SKILL / "scripts").glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            fail(errors, f"Python compile failed for {script.name}: {exc}")
            continue
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or "usage:" not in result.stdout.lower():
            fail(errors, f"--help smoke test failed for {script.name}")

    capacity_fixture = {
        "runtime_active_limit": 4,
        "runtime_active_agents": ["/root"],
        "runtime_snapshot_source": "collaboration.list_agents",
        "company_policy_version": "company-v5",
        "decision_level": 2,
        "mandatory_human_gate": False,
        "founder_discovery_required": True,
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
                "requires_separation_of_duties": False,
                "lifecycle_stage": "discovery",
                "cognitive_mode": "reuse-first-research",
                "parallelizable": True,
                "independent": True,
            }
        ],
    }
    studio_fixture = json.loads(
        (SKILL / "assets" / "studio-state.template.json").read_text(encoding="utf-8")
    )
    studio_fixture["as_of"] = date.today().isoformat()

    with tempfile.TemporaryDirectory(prefix="persistent-ai-studio-") as temp_dir:
        temp = Path(temp_dir)
        smoke_cases = (
            ("plan_capacity.py", capacity_fixture),
            ("plan_portfolio.py", studio_fixture),
        )
        for script_name, fixture in smoke_cases:
            input_path = temp / f"{script_name}.json"
            input_path.write_text(json.dumps(fixture), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SKILL / "scripts" / script_name), str(input_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                fail(errors, f"runtime smoke test failed for {script_name}: {result.stderr.strip()}")
                continue
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                fail(errors, f"runtime smoke test returned invalid JSON for {script_name}: {exc}")
                continue
            if not isinstance(output, dict):
                fail(errors, f"runtime smoke test returned a non-object for {script_name}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    file_count = sum(1 for path in SKILL.rglob("*") if path.is_file())
    print(f"Validated {file_count} skill files at {SKILL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
