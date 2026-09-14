# Compatibility and evidence

| Environment or capability | Status | Evidence and limit |
| --- | --- | --- |
| Repository and standalone ZIP | Verified for 1.0.3 | Validation checks required files, metadata, references, templates, Python syntax, CLI help, planner smoke cases, PowerShell parsing in CI, archive bytes, and checksum. |
| Codex Skill discovery | Package-compatible | The directory follows the local Skill layout. A named, repeatable end-to-end host evaluation is not yet published as a repository artifact. |
| Other Agent Skills hosts | Portable serial workflow | Hosts must preserve relative files and provide equivalent file and command capabilities. Discovery and rule routing must be verified separately. |
| Multi-agent organization | Capability-dependent | Requires live roster, create, message, wait, interrupt, reuse, and isolated workspace/context capabilities. |
| Serial role fallback | Supported by contract | Governance roles may run sequentially when independent agents are unavailable; the result must not claim independent assurance. |
| Portfolio or capacity recommendation | Decision support | Deterministic planners explain routing inputs; they do not prove market demand, product value, authorization, or delivery success. |

When recording a successful run, name the host and version, Skill release or commit, available agent/workspace isolation, planner inputs, validations actually executed, and any missing real-world evidence.
