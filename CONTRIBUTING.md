# Contributing

Issues and pull requests are welcome. Changes should preserve human root authority, deterministic routing, least authority for child agents, isolated concurrent writes, evidence-based integration, and persistent product stewardship.

## Development

1. Edit only the installable package under `skill/orchestrate-agent-organization/`.
2. Keep repository documentation outside that package.
3. Preserve parity between Python and PowerShell implementations when changing planner or validator behavior.
4. Add or update templates and reference contracts together when their schema changes.
5. Run the release audit:

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_release.py
```

On a PowerShell host, also parse every `.ps1` file:

```powershell
$failed = $false
Get-ChildItem skill/orchestrate-agent-organization/scripts -Filter *.ps1 | ForEach-Object {
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors)
  if ($errors.Count -gt 0) {
    $failed = $true
    $errors | ForEach-Object { Write-Error $_ }
  }
}
if ($failed) { exit 1 }
```

## Pull request checklist

- Explain the user or organizational failure mode the change addresses.
- Identify affected contracts, state, permissions, and lifecycle stages.
- Include deterministic validation or a falsifiable manual test.
- Avoid host-specific absolute paths, secrets, generated files, and transcripts.
- Update both English and Chinese public documentation when behavior visible to users changes.
