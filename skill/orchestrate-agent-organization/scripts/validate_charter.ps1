param(
    [Parameter(Mandatory = $true)] [string]$Parent,
    [Parameter(Mandatory = $true)] [string]$Child
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$budgetKeys = @("token_units", "cash", "compute_units")
$lifecycleStages = @("control", "discovery", "design", "build", "integrate", "verify", "release", "operate", "maintain", "debug", "evolve", "retire")
$cognitiveModes = @("organizational-control", "portfolio-stewardship", "founder-partner", "product-discovery", "reuse-first-research", "architecture-first-principles", "implementation", "adversarial-review", "test-and-falsify", "debug-and-incident", "maintenance-stewardship", "security-abuse", "operations-reliability", "integration-release")
$learningAuthorities = @("none", "propose", "commit-approved")
$supportedCompanyPolicyVersion = "company-v5"
$authoritativeRuntimeSource = "collaboration.list_agents"
$writeScopeModes = @("read-only", "isolated-worktree")
$requiredChildFields = @(
    "id", "parent_id", "mission", "deliverables", "success_criteria",
    "company_policy_version", "lifecycle_stage", "cognitive_mode",
    "context_budget_units", "artifact_budget_units", "context_sources", "learning_authority",
    "token_tier", "permissions", "delegable_permissions", "budget",
    "spawn_quota", "current_depth", "max_depth", "ttl_minutes",
    "auditor_id", "auditor_independence", "write_scope_mode", "write_scope",
    "workspace_id", "stop_conditions"
)

function Get-Value {
    param($Object, [string]$Name, $Default)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Add-Error {
    param([System.Collections.Generic.List[string]]$Errors, [string]$Message)
    $Errors.Add($Message)
}

function Get-StringPropertySet {
    param($Object, [string]$Name, [string]$Label, [System.Collections.Generic.List[string]]$Errors)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        Add-Error $Errors "$Label must be an array of strings"
        return @{}
    }
    if ($property.Value -isnot [System.Array]) {
        Add-Error $Errors "$Label must be an array of non-empty strings"
        return @{}
    }
    $items = @($property.Value)
    if (@($items | Where-Object { $_ -isnot [string] -or [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
        Add-Error $Errors "$Label must be an array of non-empty strings"
        return @{}
    }
    $set = @{}
    foreach ($item in $items) {
        $normalized = $item.Trim()
        if ($set.ContainsKey($normalized)) { Add-Error $Errors "$Label must not contain duplicates" }
        $set[$normalized] = $true
    }
    return $set
}

function Get-RepositoryScopeSet {
    param($Object, [string]$Name, [string]$Label, [System.Collections.Generic.List[string]]$Errors)
    $raw = Get-StringPropertySet $Object $Name $Label $Errors
    $result = @{}
    foreach ($scope in $raw.Keys) {
        $normalized = $scope.Replace("\", "/").Trim("/")
        $parts = @($normalized -split "/")
        $invalidPart = @($parts | Where-Object { $_ -eq "" -or $_ -eq "." -or $_ -eq ".." }).Count -gt 0
        if ([string]::IsNullOrWhiteSpace($normalized) -or $scope.StartsWith("/") -or $scope.StartsWith("\") -or $parts[0].Contains(":") -or $invalidPart) {
            Add-Error $Errors "$Label entries must be repository-relative normalized paths"
        }
        else { $result[$normalized] = $true }
    }
    return $result
}

function Test-ScopeOverlap {
    param([string]$Left, [string]$Right)
    return $Left -eq $Right -or $Left.StartsWith("$Right/") -or $Right.StartsWith("$Left/")
}

function Get-NonNegativeInt {
    param($Value, [string]$Label, [System.Collections.Generic.List[string]]$Errors)
    if ($Value -is [bool] -or ($Value -isnot [int] -and $Value -isnot [long]) -or [int64]$Value -lt 0) {
        Add-Error $Errors "$Label must be a non-negative integer"
        return 0
    }
    return [int]$Value
}

function Get-Budget {
    param($Value, [string]$Label, [System.Collections.Generic.List[string]]$Errors)
    $result = @{}
    if ($null -eq $Value -or $Value -isnot [pscustomobject]) {
        Add-Error $Errors "$Label must be an object"
        foreach ($key in $budgetKeys) { $result[$key] = 0.0 }
        return $result
    }
    foreach ($key in $budgetKeys) {
        $item = Get-Value $Value $key 0
        if ($item -is [bool] -or ($item -isnot [int] -and $item -isnot [long] -and $item -isnot [double] -and $item -isnot [decimal]) -or [double]$item -lt 0) {
            Add-Error $Errors "$Label.$key must be a non-negative number"
            $result[$key] = 0.0
        }
        else { $result[$key] = [double]$item }
    }
    return $result
}

try {
    $parentData = Get-Content -LiteralPath $Parent -Raw | ConvertFrom-Json
    $childData = Get-Content -LiteralPath $Child -Raw | ConvertFrom-Json
    if ($null -eq $parentData -or $parentData -isnot [pscustomobject]) { throw "$Parent must contain a JSON object" }
    if ($null -eq $childData -or $childData -isnot [pscustomobject]) { throw "$Child must contain a JSON object" }

    $errors = [System.Collections.Generic.List[string]]::new()
    $warnings = [System.Collections.Generic.List[string]]::new()

    $missing = @($requiredChildFields | Where-Object { $null -eq $childData.PSObject.Properties[$_] })
    if ($missing.Count -gt 0) { Add-Error $errors ("child is missing required fields: " + ($missing -join ", ")) }

    $parentId = Get-Value $parentData "id" $null
    $childId = Get-Value $childData "id" $null
    if ($parentId -isnot [string] -or [string]::IsNullOrWhiteSpace($parentId)) { Add-Error $errors "parent.id must be a non-empty string" }
    if ($childId -isnot [string] -or [string]::IsNullOrWhiteSpace($childId)) { Add-Error $errors "child.id must be a non-empty string" }
    if ((Get-Value $childData "parent_id" $null) -ne $parentId) { Add-Error $errors "child.parent_id must equal parent.id" }
    if ($childId -eq $parentId) { Add-Error $errors "child.id must differ from parent.id" }
    $mission = Get-Value $childData "mission" $null
    if ($mission -isnot [string] -or [string]::IsNullOrWhiteSpace($mission)) { Add-Error $errors "child.mission must be a non-empty string" }

    $runtimeSource = Get-Value $parentData "runtime_snapshot_source" $null
    if ($runtimeSource -isnot [string] -or [string]::IsNullOrWhiteSpace($runtimeSource)) { Add-Error $errors "parent.runtime_snapshot_source must be a non-empty string" }
    elseif ($runtimeSource -ne $authoritativeRuntimeSource) { Add-Error $errors "parent.runtime_snapshot_source must be $authoritativeRuntimeSource" }
    $activeAgents = Get-StringPropertySet $parentData "runtime_active_agents" "parent.runtime_active_agents" $errors
    if ($parentId -is [string] -and -not $activeAgents.ContainsKey($parentId)) { Add-Error $errors "parent.runtime_active_agents must contain parent.id" }
    $authorizedAuditors = Get-StringPropertySet $parentData "authorized_auditor_ids" "parent.authorized_auditor_ids" $errors
    $inactiveAuditors = @($authorizedAuditors.Keys | Where-Object { -not $activeAgents.ContainsKey($_) } | Sort-Object)
    if ($inactiveAuditors.Count -gt 0) { Add-Error $errors ("parent.authorized_auditor_ids contains inactive ids: " + ($inactiveAuditors -join ", ")) }

    $parentPolicy = Get-Value $parentData "company_policy_version" $null
    $childPolicy = Get-Value $childData "company_policy_version" $null
    if ($parentPolicy -ne $supportedCompanyPolicyVersion) { Add-Error $errors "parent.company_policy_version must be $supportedCompanyPolicyVersion" }
    if ($childPolicy -ne $supportedCompanyPolicyVersion) { Add-Error $errors "child.company_policy_version must be $supportedCompanyPolicyVersion" }
    elseif ($childPolicy -ne $parentPolicy) { Add-Error $errors "child.company_policy_version must equal parent.company_policy_version" }
    if ($lifecycleStages -notcontains (Get-Value $childData "lifecycle_stage" $null)) { Add-Error $errors "child.lifecycle_stage is not allowed" }
    if ($cognitiveModes -notcontains (Get-Value $childData "cognitive_mode" $null)) { Add-Error $errors "child.cognitive_mode is not allowed" }

    $contextBudget = Get-Value $childData "context_budget_units" $null
    if ($contextBudget -is [bool] -or ($contextBudget -isnot [int] -and $contextBudget -isnot [long]) -or [int64]$contextBudget -lt 1 -or [int64]$contextBudget -gt 8) {
        Add-Error $errors "child.context_budget_units must be an integer from 1 to 8"
    }
    $artifactBudget = Get-Value $childData "artifact_budget_units" $null
    if ($artifactBudget -is [bool] -or ($artifactBudget -isnot [int] -and $artifactBudget -isnot [long]) -or [int64]$artifactBudget -lt 1 -or [int64]$artifactBudget -gt 8) {
        Add-Error $errors "child.artifact_budget_units must be an integer from 1 to 8"
    }
    $contextSources = Get-StringPropertySet $childData "context_sources" "child.context_sources" $errors
    if ($contextSources.Count -eq 0) { Add-Error $errors "child.context_sources must contain at least one scoped source" }
    $learningAuthority = Get-Value $childData "learning_authority" $null
    if ($learningAuthorities -notcontains $learningAuthority) { Add-Error $errors "child.learning_authority must be none, propose, or commit-approved" }

    $tokenTier = Get-Value $childData "token_tier" $null
    if (@("low", "medium", "high", "very-high") -notcontains $tokenTier) {
        Add-Error $errors "child.token_tier must be low, medium, high, or very-high"
    }

    $parentDelegable = Get-StringPropertySet $parentData "delegable_permissions" "parent.delegable_permissions" $errors
    $childPermissions = Get-StringPropertySet $childData "permissions" "child.permissions" $errors
    $childDelegable = Get-StringPropertySet $childData "delegable_permissions" "child.delegable_permissions" $errors
    $excessPermissions = @($childPermissions.Keys | Where-Object { -not $parentDelegable.ContainsKey($_) } | Sort-Object)
    if ($excessPermissions.Count -gt 0) { Add-Error $errors ("child permissions exceed parent delegation: " + ($excessPermissions -join ", ")) }
    $excessDelegable = @($childDelegable.Keys | Where-Object { -not $childPermissions.ContainsKey($_) } | Sort-Object)
    if ($excessDelegable.Count -gt 0) { Add-Error $errors ("child delegates permissions it does not hold: " + ($excessDelegable -join ", ")) }
    if ($learningAuthority -eq "commit-approved" -and -not $childPermissions.ContainsKey("memory:write-approved")) {
        Add-Error $errors "child.learning_authority commit-approved requires memory:write-approved permission"
    }

    $writeScopeMode = Get-Value $childData "write_scope_mode" $null
    if ($writeScopeModes -notcontains $writeScopeMode) { Add-Error $errors "child.write_scope_mode must be read-only or isolated-worktree" }
    $writeScopes = Get-RepositoryScopeSet $childData "write_scope" "child.write_scope" $errors
    $workspaceId = Get-Value $childData "workspace_id" $null
    if ($workspaceId -isnot [string] -or [string]::IsNullOrWhiteSpace($workspaceId)) { Add-Error $errors "child.workspace_id must be a non-empty string"; $workspaceId = "" }
    else { $workspaceId = $workspaceId.Trim() }
    $authorizedWorkspaces = Get-StringPropertySet $parentData "authorized_workspace_ids" "parent.authorized_workspace_ids" $errors
    $reservedWorkspaces = Get-StringPropertySet $parentData "reserved_workspace_ids" "parent.reserved_workspace_ids" $errors
    $reservedScopes = Get-RepositoryScopeSet $parentData "reserved_write_scopes" "parent.reserved_write_scopes" $errors
    $workspaceWrite = @($childPermissions.Keys | Where-Object { $_.EndsWith(":write") -and -not $_.StartsWith("memory:") }).Count -gt 0
    if ($workspaceWrite) {
        if ($writeScopeMode -ne "isolated-worktree") { Add-Error $errors "write-capable child requires isolated-worktree write_scope_mode" }
        if ($writeScopes.Count -eq 0) { Add-Error $errors "write-capable child requires at least one write_scope" }
        if ($workspaceId -eq "none") { Add-Error $errors "write-capable child requires a runtime-issued workspace_id" }
        if (-not [string]::IsNullOrWhiteSpace($workspaceId) -and -not $authorizedWorkspaces.ContainsKey($workspaceId)) { Add-Error $errors "child.workspace_id is not authorized by the parent runtime roster" }
        if ($reservedWorkspaces.ContainsKey($workspaceId)) { Add-Error $errors "child.workspace_id is already reserved" }
        foreach ($scope in $writeScopes.Keys) {
            foreach ($reserved in $reservedScopes.Keys) {
                if (Test-ScopeOverlap $scope $reserved) { Add-Error $errors "child.write_scope overlaps a reserved scope: $scope"; break }
            }
        }
    }
    else {
        if ($writeScopeMode -ne "read-only") { Add-Error $errors "non-writing child must use read-only write_scope_mode" }
        if ($writeScopes.Count -gt 0) { Add-Error $errors "non-writing child must have an empty write_scope" }
        if (-not [string]::IsNullOrWhiteSpace($workspaceId) -and $workspaceId -ne "none") { Add-Error $errors "non-writing child.workspace_id must be none" }
    }

    $parentBudget = Get-Budget (Get-Value $parentData "budget" $null) "parent.budget" $errors
    $reservedBudget = Get-Budget (Get-Value $parentData "reserved_budget" ([pscustomobject]@{})) "parent.reserved_budget" $errors
    $childBudget = Get-Budget (Get-Value $childData "budget" $null) "child.budget" $errors
    foreach ($key in $budgetKeys) {
        if ($reservedBudget[$key] -gt $parentBudget[$key]) { Add-Error $errors "parent.reserved_budget.$key exceeds parent.budget.$key" }
        if ($reservedBudget[$key] + $childBudget[$key] -gt $parentBudget[$key]) { Add-Error $errors "reserved plus child budget for $key exceeds parent.budget.$key" }
    }

    $parentQuota = Get-NonNegativeInt (Get-Value $parentData "spawn_quota" 0) "parent.spawn_quota" $errors
    $reservedSpawn = Get-NonNegativeInt (Get-Value $parentData "reserved_spawn_units" 0) "parent.reserved_spawn_units" $errors
    $childQuota = Get-NonNegativeInt (Get-Value $childData "spawn_quota" 0) "child.spawn_quota" $errors
    if ($reservedSpawn + 1 + $childQuota -gt $parentQuota) { Add-Error $errors "child and descendant reservations exceed parent.spawn_quota" }

    $parentDepth = Get-NonNegativeInt (Get-Value $parentData "current_depth" 0) "parent.current_depth" $errors
    $childDepth = Get-NonNegativeInt (Get-Value $childData "current_depth" 0) "child.current_depth" $errors
    $parentMaxDepth = Get-NonNegativeInt (Get-Value $parentData "max_depth" 0) "parent.max_depth" $errors
    $childMaxDepth = Get-NonNegativeInt (Get-Value $childData "max_depth" 0) "child.max_depth" $errors
    if ($childDepth -ne $parentDepth + 1) { Add-Error $errors "child.current_depth must equal parent.current_depth + 1" }
    if ($childDepth -gt $parentMaxDepth) { Add-Error $errors "child depth exceeds parent.max_depth" }
    if ($parentDepth -gt $parentMaxDepth) { Add-Error $errors "parent.current_depth exceeds parent.max_depth" }
    if ($childDepth -gt $childMaxDepth) { Add-Error $errors "child.current_depth exceeds child.max_depth" }
    if ($childMaxDepth -gt $parentMaxDepth) { Add-Error $errors "child.max_depth exceeds parent.max_depth" }
    if ($childQuota -gt 0 -and $childDepth -ge $childMaxDepth) { Add-Error $errors "positive child.spawn_quota requires remaining descendant depth" }

    $parentTtl = Get-NonNegativeInt (Get-Value $parentData "ttl_minutes" 0) "parent.ttl_minutes" $errors
    $childTtl = Get-NonNegativeInt (Get-Value $childData "ttl_minutes" 0) "child.ttl_minutes" $errors
    if ($childTtl -eq 0) { Add-Error $errors "child.ttl_minutes must be positive" }
    if ($parentTtl -gt 0 -and $childTtl -gt $parentTtl) { Add-Error $errors "child.ttl_minutes exceeds parent lease" }

    $auditorId = Get-Value $childData "auditor_id" $null
    if ($auditorId -isnot [string] -or [string]::IsNullOrWhiteSpace($auditorId)) { Add-Error $errors "child.auditor_id must be a non-empty string" }
    else {
        $auditorId = $auditorId.Trim()
        if ($auditorId -eq $childId) { Add-Error $errors "a child cannot be its own auditor" }
        if (-not $authorizedAuditors.ContainsKey($auditorId)) { Add-Error $errors "child.auditor_id is not an authorized active auditor" }
    }
    $auditorIndependence = Get-Value $childData "auditor_independence" $null
    if (@("parent-accountable", "independent-assurance") -notcontains $auditorIndependence) { Add-Error $errors "child.auditor_independence must be parent-accountable or independent-assurance" }
    elseif ($auditorIndependence -eq "parent-accountable" -and $auditorId -ne $parentId) { Add-Error $errors "parent-accountable auditor must equal parent.id" }
    elseif ($auditorIndependence -eq "independent-assurance" -and $auditorId -eq $parentId) { Add-Error $errors "independent-assurance auditor must differ from parent.id" }

    foreach ($field in @("deliverables", "success_criteria", "stop_conditions")) {
        $value = Get-StringPropertySet $childData $field "child.$field" $errors
        if ($value.Count -eq 0) { Add-Error $errors "child.$field must be a non-empty array" }
    }
    if ($childQuota -gt 0 -and $childDelegable.Count -eq 0) { $warnings.Add("child can spawn descendants but has no delegable permissions") }
    if ($childBudget["token_units"] -eq 0) { $warnings.Add("child token allocation is zero; the control plane should replan") }

    [ordered]@{
        valid = $errors.Count -eq 0
        errors = @($errors)
        warnings = @($warnings)
    } | ConvertTo-Json -Depth 6
    if ($errors.Count -gt 0) { exit 2 }
    exit 0
}
catch {
    [ordered]@{
        valid = $false
        errors = @($_.Exception.Message)
        warnings = @()
    } | ConvertTo-Json -Depth 4
    exit 2
}
