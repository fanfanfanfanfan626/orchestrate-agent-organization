# AI installation contract

Install the `orchestrate-agent-organization` skill from:

```text
https://github.com/fanfanfanfanfan626/orchestrate-agent-organization
```

Important package facts:

- The repository root is documentation and release infrastructure.
- The complete installable skill is `skill/orchestrate-agent-organization/`.
- Its entry point is `skill/orchestrate-agent-organization/SKILL.md`.
- Copy the entire skill directory without flattening it; its `agents/`, `assets/`, `references/`, and `scripts/` siblings are required.
- Do not search for a root-level `SKILL.md` and do not install only the entry file.
- Do not copy repository-level files such as `README.md`, `LICENSE`, `tools/`, or `.github/` into the host's skill directory.
- Do not overwrite an existing installation without first telling the user what will change.

For Codex, the default destination is:

```text
~/.codex/skills/orchestrate-agent-organization/
```

After copying, verify that the destination contains `SKILL.md`, then restart Codex. A valid explicit invocation is:

```text
Use $orchestrate-agent-organization to run this product as a persistent, human-led AI studio and size the organization from the actual task graph.
```

For another agent host, preserve the directory structure and make the skill entry point plus relative resources available to the agent. Full multi-agent execution requires equivalent agent-list, create, message, wait, interrupt, reuse, and isolated-workspace capabilities; otherwise operate the governed roles serially.
