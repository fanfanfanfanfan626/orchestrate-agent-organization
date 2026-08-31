param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$tokenModelVersion = "organizational-fitness-v2"
$supportedCompanyPolicyVersion = "company-v5"
$authoritativeRuntimeSources = @("collaboration.list_agents")
$founderCharterStatuses = @("not-required", "raw", "framed", "explored", "decision-ready", "authorized")
$preAuthorizationStages = @("control", "discovery", "design", "verify")
$lifecycleStages = @("control", "discovery", "design", "build", "integrate", "verify", "release", "operate", "maintain", "debug", "evolve", "retire")
$cognitiveModes = @("organizational-control", "portfolio-stewardship", "founder-partner", "product-discovery", "reuse-first-research", "architecture-first-principles", "implementation", "adversarial-review", "test-and-falsify", "debug-and-incident", "maintenance-stewardship", "security-abuse", "operations-reliability", "integration-release")
$defaultModeByStage = @{
    control = "organizational-control"; discovery = "product-discovery";
    design = "architecture-first-principles"; build = "implementation";
    integrate = "integration-release"; verify = "test-and-falsify";
    release = "integration-release"; operate = "operations-reliability";
    maintain = "maintenance-stewardship"; debug = "debug-and-incident";
    evolve = "maintenance-stewardship"; retire = "maintenance-stewardship"
}

function Get-Value {
    param($Object, [string]$Name, $Default)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Get-BoundedInt {
    param($Value, [string]$Name, [int]$Low, [int]$High)
    if ($Value -is [bool] -or ($Value -isnot [int] -and $Value -isnot [long])) {
        throw "$Name must be an integer"
    }
    $number = [int]$Value
    if ($number -lt $Low -or $number -gt $High) {
        throw "$Name must be between $Low and $High"
    }
    return $number
}

function Get-StrictBool {
    param($Value, [string]$Name)
    if ($Value -isnot [bool]) { throw "$Name must be a boolean" }
    return $Value
}

function Get-TokenTier {
    param([double]$Effort)
    if ($Effort -le 12) { return "low" }
    if ($Effort -le 30) { return "medium" }
    if ($Effort -le 60) { return "high" }
    return "very-high"
}

function Get-PropertySum {
    param([array]$Items, [string]$Property)
    $total = 0
    foreach ($item in $Items) { $total += [int]$item.$Property }
    return $total
}

try {
    $data = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
    if ($null -eq $data -or $data -is [array] -or $data -isnot [pscustomobject]) {
        throw "capacity input must be a JSON object"
    }

    $activeLimit = Get-BoundedInt (Get-Value $data "runtime_active_limit" 1) "runtime_active_limit" 1 256
    $snapshotSource = Get-Value $data "runtime_snapshot_source" "unspecified"
    if ($snapshotSource -isnot [string] -or [string]::IsNullOrWhiteSpace($snapshotSource)) {
        throw "runtime_snapshot_source must be a non-empty string"
    }
    if (@($authoritativeRuntimeSources + "unspecified") -notcontains $snapshotSource) {
        throw "runtime_snapshot_source is not allowed"
    }

    $rawAgentsProperty = $data.PSObject.Properties["runtime_active_agents"]
    $activeAgents = @()
    $snapshotAuthoritative = $false
    if ($null -ne $rawAgentsProperty) {
        if ($rawAgentsProperty.Value -isnot [System.Array]) {
            throw "runtime_active_agents must be a non-empty array of agent names"
        }
        $activeAgents = @($rawAgentsProperty.Value)
        if ($activeAgents.Count -eq 0) {
            throw "runtime_active_agents must be a non-empty array of agent names"
        }
        foreach ($agent in $activeAgents) {
            if ($agent -isnot [string] -or [string]::IsNullOrWhiteSpace($agent)) {
                throw "runtime_active_agents must be a non-empty array of agent names"
            }
        }
        $activeAgents = @($activeAgents | ForEach-Object { $_.Trim() })
        if (@($activeAgents | Select-Object -Unique).Count -ne $activeAgents.Count) {
            throw "runtime_active_agents must not contain duplicates"
        }
        $activeNow = $activeAgents.Count
        $suppliedNowProperty = $data.PSObject.Properties["runtime_active_now"]
        if ($null -ne $suppliedNowProperty) {
            $suppliedNow = Get-BoundedInt $suppliedNowProperty.Value "runtime_active_now" 1 256
            if ($suppliedNow -ne $activeNow) {
                throw "runtime_active_now conflicts with runtime_active_agents"
            }
        }
        if ($authoritativeRuntimeSources -notcontains $snapshotSource) {
            throw "runtime_snapshot_source is not an allowed authoritative source; runtime_active_agents requires collaboration.list_agents"
        }
        $snapshotAuthoritative = $true
    }
    else {
        if ($snapshotSource -ne "unspecified") {
            throw "runtime_active_agents is required for an authoritative runtime source"
        }
        $activeNow = Get-BoundedInt (Get-Value $data "runtime_active_now" 1) "runtime_active_now" 1 256
    }
    if ($activeNow -gt $activeLimit) {
        throw "active runtime occupancy exceeds runtime_active_limit"
    }

    $decisionLevel = Get-BoundedInt (Get-Value $data "decision_level" 1) "decision_level" 0 5
    $companyPolicyVersion = Get-Value $data "company_policy_version" $supportedCompanyPolicyVersion
    if ($companyPolicyVersion -ne $supportedCompanyPolicyVersion) {
        throw "company_policy_version must be $supportedCompanyPolicyVersion"
    }
    $mandatoryHumanGate = Get-StrictBool (Get-Value $data "mandatory_human_gate" $false) "mandatory_human_gate"
    $founderDiscoveryRequired = Get-StrictBool (Get-Value $data "founder_discovery_required" $false) "founder_discovery_required"
    $defaultFounderStatus = if ($founderDiscoveryRequired) { "raw" } else { "not-required" }
    $founderCharterStatus = Get-Value $data "founder_charter_status" $defaultFounderStatus
    if ($founderCharterStatuses -notcontains $founderCharterStatus) {
        throw "founder_charter_status is not allowed"
    }
    if ($founderDiscoveryRequired -and $founderCharterStatus -eq "not-required") {
        throw "founder_charter_status cannot be not-required when discovery is required"
    }
    if (-not $founderDiscoveryRequired -and $founderCharterStatus -ne "not-required") {
        throw "founder_charter_status must be not-required when discovery is not required"
    }
    $founderAuthorized = -not $founderDiscoveryRequired -or $founderCharterStatus -eq "authorized"
    $physicalFreeChildSlots = [math]::Max(0, $activeLimit - $activeNow)
    if ($snapshotAuthoritative) { $freeChildSlots = $physicalFreeChildSlots }
    else { $freeChildSlots = [math]::Min(1, $physicalFreeChildSlots) }

    $rawItems = @(Get-Value $data "items" @())
    if ($rawItems.Count -eq 0) { throw "items must be a non-empty array" }
    $seen = @{}
    $items = @()
    for ($index = 0; $index -lt $rawItems.Count; $index++) {
        $item = $rawItems[$index]
        if ($null -eq $item -or $item -isnot [pscustomobject]) {
            throw "items[$index] must be an object"
        }
        $itemId = Get-Value $item "id" $null
        if ($itemId -isnot [string] -or [string]::IsNullOrWhiteSpace($itemId)) {
            throw "items[$index].id must be a non-empty string"
        }
        $itemId = $itemId.Trim()
        if ($seen.ContainsKey($itemId)) { throw "duplicate item id: $itemId" }
        $seen[$itemId] = $true

        $complexity = Get-BoundedInt (Get-Value $item "complexity" 1) "$itemId.complexity" 1 5
        $risk = Get-BoundedInt (Get-Value $item "risk" 0) "$itemId.risk" 0 4
        $estimatedUnits = Get-BoundedInt (Get-Value $item "estimated_units" 1) "$itemId.estimated_units" 1 8
        $contextUnits = Get-BoundedInt (Get-Value $item "context_units" $complexity) "$itemId.context_units" 1 5
        $parallelizable = Get-StrictBool (Get-Value $item "parallelizable" $false) "$itemId.parallelizable"
        $independent = Get-StrictBool (Get-Value $item "independent" $false) "$itemId.independent"
        $defaultCoupling = if ($parallelizable -and $independent) { 1 } else { 4 }
        $coupling = Get-BoundedInt (Get-Value $item "coupling" $defaultCoupling) "$itemId.coupling" 0 4
        $defaultContextIsolation = if ($independent) { [math]::Max(0, $contextUnits - 2) } else { 0 }
        $contextIsolation = Get-BoundedInt (Get-Value $item "context_isolation" $defaultContextIsolation) "$itemId.context_isolation" 0 4
        $specialistNeed = Get-BoundedInt (Get-Value $item "specialist_need" 0) "$itemId.specialist_need" 0 4
        $defaultCriticalPath = if ($parallelizable) { 1 } else { 0 }
        $criticalPath = Get-BoundedInt (Get-Value $item "critical_path" $defaultCriticalPath) "$itemId.critical_path" 0 4
        $requiresSeparation = Get-StrictBool (Get-Value $item "requires_separation_of_duties" $false) "$itemId.requires_separation_of_duties"
        $requiresIndependentVerification = Get-StrictBool (Get-Value $item "requires_independent_verification" $false) "$itemId.requires_independent_verification"
        $lifecycleStage = Get-Value $item "lifecycle_stage" "design"
        if ($lifecycleStages -notcontains $lifecycleStage) {
            throw "$itemId.lifecycle_stage is not allowed"
        }
        $cognitiveMode = Get-Value $item "cognitive_mode" $defaultModeByStage[$lifecycleStage]
        if ($cognitiveModes -notcontains $cognitiveMode) {
            throw "$itemId.cognitive_mode is not allowed"
        }
        $effort = $complexity * $estimatedUnits + $contextUnits + 2 * $risk
        $focusRatePoints = [math]::Min(30, 4 * ($complexity - 1) + 3 * ($contextUnits - 1) + $(if ($independent) { 3 } else { 0 }))
        $focusSavings = [math]::Max(0, [math]::Round($effort * $focusRatePoints / 100))
        $contextPacketOverhead = 1 + [math]::Ceiling($contextUnits / 2) + $coupling
        $interfaceIntegrationOverhead = 2 + $coupling
        $netDelegationSavings = $focusSavings - $contextPacketOverhead - $interfaceIntegrationOverhead
        $qualityGain = 2 * $contextIsolation + 2 * $specialistNeed + 2 * [math]::Max(0, $complexity - 3)
        $criticalPathGain = $criticalPath * [math]::Max(1, [math]::Ceiling($estimatedUnits / 3))
        $controlGain = if ($requiresSeparation) { 10 } else { 0 }
        $organizationValue = $netDelegationSavings + $qualityGain + $criticalPathGain + $controlGain
        $selectionDrivers = @()
        if ($netDelegationSavings -gt 0) { $selectionDrivers += "token-efficiency" }
        if ($contextIsolation -gt 0) { $selectionDrivers += "context-isolation" }
        if ($specialistNeed -gt 0) { $selectionDrivers += "specialist-capability" }
        if ($criticalPath -gt 0) { $selectionDrivers += "critical-path-latency" }
        if ($requiresSeparation) { $selectionDrivers += "separation-of-duties" }
        $items += [pscustomobject][ordered]@{
            id = $itemId
            complexity = $complexity
            risk = $risk
            estimated_units = $estimatedUnits
            context_units = $contextUnits
            parallelizable = $parallelizable
            independent = $independent
            coupling = $coupling
            context_isolation = $contextIsolation
            specialist_need = $specialistNeed
            critical_path = $criticalPath
            requires_separation_of_duties = $requiresSeparation
            lifecycle_stage = $lifecycleStage
            cognitive_mode = $cognitiveMode
            requires_independent_verification = $requiresIndependentVerification
            effort = $effort
            focus_savings = [int]$focusSavings
            context_packet_overhead = [int]$contextPacketOverhead
            integration_overhead = [int]$interfaceIntegrationOverhead
            net_delegation_savings = [int]$netDelegationSavings
            quality_gain = [int]$qualityGain
            critical_path_gain = [int]$criticalPathGain
            control_gain = [int]$controlGain
            organization_value = [int]$organizationValue
            selection_drivers = @($selectionDrivers)
        }
    }

    if (-not $founderAuthorized) {
        $disallowed = @($items | Where-Object { $preAuthorizationStages -notcontains $_.lifecycle_stage } | ForEach-Object { $_.id } | Sort-Object)
        if ($disallowed.Count -gt 0) {
            throw "pre-authorization capacity input contains implementation stages: $($disallowed -join ', ')"
        }
    }

    $potentialCandidates = @($items | Where-Object {
        $_.parallelizable -and $_.independent -and $_.effort -ge 6
    })
    $tokenEfficientCandidates = @($potentialCandidates | Where-Object { $_.net_delegation_savings -gt 0 })
    $candidates = @($potentialCandidates | Where-Object { $_.organization_value -gt 0 } |
        Sort-Object -Property @{Expression = "organization_value"; Descending = $true}, @{Expression = "effort"; Descending = $true}, @{Expression = "risk"; Descending = $true}, @{Expression = "id"; Descending = $false})
    $materialRisk = @($items | Where-Object {
        $_.risk -ge 3 -or $_.requires_independent_verification
    }).Count -gt 0
    $parallelEffort = Get-PropertySum $candidates "effort"
    $totalEffort = (Get-PropertySum $items "effort") + [math]::Max(0, $items.Count - 1) * 2

    $expectedReworkRaw = 0.0
    foreach ($item in $items) {
        $expectedReworkRaw += $item.risk * ($item.complexity + $item.estimated_units + $item.context_units) / 4
        if ($item.requires_independent_verification) { $expectedReworkRaw += 4 }
    }
    $expectedReworkUnits = [int][math]::Ceiling($expectedReworkRaw)
    $verificationWeight = 0
    foreach ($item in $items) {
        if ($item.risk -ge 3 -or $item.requires_independent_verification) {
            $verificationWeight += 2 * ($item.risk + 1)
        }
    }
    $verificationWeight = [math]::Max(6, $verificationWeight)
    $expectedReworkAvoidance = if ($materialRisk) { [int][math]::Round($expectedReworkUnits * 0.70) } else { 0 }
    $verifierRequired = @($items | Where-Object { $_.requires_independent_verification }).Count -gt 0 -or ($decisionLevel -ge 2 -and $materialRisk)
    $verifierTokenEfficient = $expectedReworkAvoidance -ge $verificationWeight

    $verifierCount = 0
    if ($materialRisk -and $freeChildSlots -gt 0 -and ($verifierRequired -or $verifierTokenEfficient)) { $verifierCount = 1 }
    $workerCapacity = [math]::Max(0, $freeChildSlots - $verifierCount)
    $orchestrationOnlyLead = $parallelEffort -ge 30 -or $candidates.Count -ge 4
    $desiredWorkers = 0
    if ($candidates.Count -ge 2) {
        if ($orchestrationOnlyLead) { $desiredWorkers = $candidates.Count }
        else { $desiredWorkers = $candidates.Count - 1 }
    }
    elseif ($candidates.Count -eq 1 -and $items.Count -ge 2) { $desiredWorkers = 1 }
    $workerCount = [math]::Min($workerCapacity, $desiredWorkers)
    if ($mandatoryHumanGate) {
        $workerCount = 0
        $verifierCount = 0
    }

    $delegated = @()
    if ($workerCount -gt 0) { $delegated = @($candidates | Select-Object -First $workerCount) }
    $delegatedIds = @{}
    foreach ($item in $delegated) { $delegatedIds[$item.id] = $true }
    $leadItems = @($items | Where-Object { -not $delegatedIds.ContainsKey($_.id) })
    $recommendedChildren = $workerCount + $verifierCount

    $decompositionDifficultySavings = Get-PropertySum $delegated "focus_savings"
    $contextPacketTotal = Get-PropertySum $delegated "context_packet_overhead"
    $integrationOverheadTotal = Get-PropertySum $delegated "integration_overhead"
    $appliedReworkAvoidance = if ($verifierCount -gt 0) { $expectedReworkAvoidance } else { 0 }
    $appliedVerificationWeight = if ($verifierCount -gt 0) { $verificationWeight } else { 0 }
    $singleAgentExpectedTokens = $totalEffort + $expectedReworkUnits
    $selectedPlanExpectedTokens = [math]::Max(1, $singleAgentExpectedTokens - $decompositionDifficultySavings + $contextPacketTotal + $integrationOverheadTotal + $appliedVerificationWeight - $appliedReworkAvoidance)
    $estimatedTokenSavings = $singleAgentExpectedTokens - $selectedPlanExpectedTokens
    $estimatedTokenSavingsPercent = [math]::Round($estimatedTokenSavings * 100 / $singleAgentExpectedTokens, 1)
    $selectedQualityGain = Get-PropertySum $delegated "quality_gain"
    $selectedCriticalPathGain = Get-PropertySum $delegated "critical_path_gain"
    $selectedControlGain = Get-PropertySum $delegated "control_gain"
    $selectedOrganizationValue = $estimatedTokenSavings + $selectedQualityGain + $selectedCriticalPathGain + $selectedControlGain

    $reasons = @()
    if (-not $snapshotAuthoritative) {
        $reasons += "Runtime occupancy is non-authoritative; creation is conservatively capped at one child."
    }
    if ($mandatoryHumanGate) {
        $reasons += "A mandatory human gate is open; no child may be activated before it is resolved."
    }
    elseif (-not $founderAuthorized) {
        $reasons += "The Founder Charter is not authorized; only reversible discovery, design, and assurance work may proceed."
    }
    elseif ($freeChildSlots -eq 0) {
        $reasons += "Runtime has no free child slot; the lead must execute and verify serially."
    }
    elseif ($potentialCandidates.Count -eq 0) {
        $reasons += "No substantive independent workstream is available for focused delegation."
    }
    elseif ($candidates.Count -eq 0) {
        $reasons += "Independent work exists, but its token, quality, latency, specialist, and control benefits do not exceed coordination cost."
    }
    elseif ($workerCount -gt 0) {
        $noun = if ($workerCount -eq 1) { "child" } else { "children" }
        $driverNames = @($delegated | ForEach-Object { $_.selection_drivers } | Sort-Object -Unique)
        $executionTokenDelta = $decompositionDifficultySavings - $contextPacketTotal - $integrationOverheadTotal
        $reasons += "$($candidates.Count) organizationally valuable workstreams justify $workerCount worker $noun for $($driverNames -join ', '); net execution token delta (positive means savings) is $executionTokenDelta units before assurance."
    }
    if ($materialRisk -and $verifierCount -gt 0) {
        $assuranceDelta = $appliedReworkAvoidance - $appliedVerificationWeight
        if ($assuranceDelta -ge 0) {
            $reasons += "Independent assurance is estimated to avoid $appliedReworkAvoidance rework units at a cost of $appliedVerificationWeight, saving $assuranceDelta token units while separating duties."
        }
        else {
            $reasons += "Independent assurance adds an estimated $(-$assuranceDelta)-unit safety premium; material D$decisionLevel risk requires the separation of duties."
        }
    }
    elseif ($materialRisk -and -not $mandatoryHumanGate) {
        if ($freeChildSlots -eq 0) {
            $reasons += "Material risk exists, but verification must run serially because capacity is full."
        }
        else {
            $reasons += "Material risk exists, but a separate verifier is neither mandated at this decision level nor estimated to reduce total tokens; apply serial challenge."
        }
    }
    if ($workerCount -lt $desiredWorkers -and -not $mandatoryHumanGate) {
        $reasons += "One or more parallel workstreams remain with the lead or queue because runtime concurrency is the binding limit."
    }

    $founderPending = $founderDiscoveryRequired -and -not $founderAuthorized
    $allocations = @()
    $leadWeight = [math]::Max(4, (Get-PropertySum $leadItems "effort") + $integrationOverheadTotal)
    $allocations += [ordered]@{
        agent = "lead"
        role = if ($founderPending) { "Founder Partner: human dialogue, synthesis, and authorization preparation" } else { "control, integration, and queued execution" }
        workstreams = @($leadItems | ForEach-Object { $_.id })
        token_weight = $leadWeight
        company_policy_version = $companyPolicyVersion
        lifecycle_stage = if ($founderPending) { "discovery" } else { "control" }
        cognitive_mode = if ($founderPending) { "founder-partner" } else { "organizational-control" }
        context_budget_units = 5
        artifact_budget_units = [math]::Min(8, [math]::Max(2, $leadItems.Count + 2))
        context_source_policy = "project map plus only sources needed for control and integration"
        learning_authority = "commit-approved"
    }
    for ($index = 0; $index -lt $delegated.Count; $index++) {
        $item = $delegated[$index]
        $allocations += [ordered]@{
            agent = "worker-$($index + 1)"
            role = "bounded mission worker"
            workstreams = @($item.id)
            token_weight = [math]::Max(4, $item.effort - $item.focus_savings + $item.context_packet_overhead)
            estimated_focus_savings = $item.focus_savings
            context_packet_overhead = $item.context_packet_overhead
            interface_coupling = $item.coupling
            estimated_organization_value = $item.organization_value
            selection_drivers = @($item.selection_drivers)
            company_policy_version = $companyPolicyVersion
            lifecycle_stage = $item.lifecycle_stage
            cognitive_mode = $item.cognitive_mode
            context_budget_units = $item.context_units
            artifact_budget_units = 2
            context_source_policy = "project map node plus scoped source, interface, test, and evidence paths"
            learning_authority = "propose"
        }
    }
    if ($verifierCount -gt 0) {
        $allocations += [ordered]@{
            agent = "verifier-1"
            role = "independent assurance"
            workstreams = @($items | Where-Object { $_.risk -ge 2 } | ForEach-Object { $_.id })
            token_weight = [math]::Max(6, $verificationWeight)
            company_policy_version = $companyPolicyVersion
            lifecycle_stage = "verify"
            cognitive_mode = "adversarial-review"
            context_budget_units = 4
            artifact_budget_units = 1
            context_source_policy = "acceptance criteria plus changed interfaces, tests, evidence, and risk paths"
            learning_authority = "propose"
        }
    }

    $totalWeight = [int](($allocations | ForEach-Object { $_.token_weight } | Measure-Object -Sum).Sum)
    $remaining = 100
    for ($index = 0; $index -lt $allocations.Count; $index++) {
        if ($index -eq $allocations.Count - 1) {
            $share = $remaining
        }
        else {
            $share = [math]::Max(1, [math]::Round($allocations[$index].token_weight * 100 / $totalWeight))
            $share = [math]::Min($share, $remaining - ($allocations.Count - $index - 1))
        }
        $allocations[$index].token_share_percent = [int]$share
        $allocations[$index].token_tier = Get-TokenTier $allocations[$index].token_weight
        $remaining -= $share
    }

    $directEligible = (
        -not $mandatoryHumanGate -and
        -not $founderPending -and
        $decisionLevel -le 1 -and
        -not $materialRisk -and
        $totalEffort -le 12 -and
        $items.Count -le 2 -and
        $candidates.Count -lt 2 -and
        $recommendedChildren -eq 0
    )
    if ($mandatoryHumanGate) { $executionRoute = "human-gated" }
    elseif ($founderPending) { $executionRoute = "founder-discovery" }
    elseif ($directEligible) { $executionRoute = "direct" }
    elseif ($recommendedChildren -gt 0) { $executionRoute = "organized" }
    else { $executionRoute = "governed-serial" }

    if ($executionRoute -eq "human-gated") { $selectedTopology = "human-gated-control-plane" }
    elseif ($executionRoute -eq "founder-discovery") {
        if ($recommendedChildren -gt 0) { $selectedTopology = "founder-office-with-advisory-cells" }
        else { $selectedTopology = "founder-office" }
    }
    elseif ($workerCount -gt 0 -and $verifierCount -gt 0) { $selectedTopology = "mission-cell-with-independent-assurance" }
    elseif ($workerCount -gt 0) { $selectedTopology = "mission-cell" }
    elseif ($verifierCount -gt 0) { $selectedTopology = "lead-with-independent-assurance" }
    else { $selectedTopology = "lead-only" }

    $result = [ordered]@{
        valid = $true
        machine_selected = $true
        execution_route = $executionRoute
        selected_topology = $selectedTopology
        load_governance_references = $executionRoute -ne "direct"
        load_organization_references = $executionRoute -ne "direct"
        load_founder_office_reference = $founderDiscoveryRequired
        decision_level = $decisionLevel
        company_policy_version = $companyPolicyVersion
        mandatory_human_gate = $mandatoryHumanGate
        founder_discovery_required = $founderDiscoveryRequired
        founder_charter_status = $founderCharterStatus
        implementation_activation_allowed = $founderAuthorized -and -not $mandatoryHumanGate
        allowed_pre_authorization_stages = @($preAuthorizationStages)
        selected_organization_token_tier = Get-TokenTier $selectedPlanExpectedTokens
        estimated_effort_points = $totalEffort
        token_model_version = $tokenModelVersion
        token_estimate_not_measured = $true
        single_agent_expected_token_units = $singleAgentExpectedTokens
        selected_plan_expected_token_units = $selectedPlanExpectedTokens
        estimated_token_savings_units = $estimatedTokenSavings
        estimated_token_savings_percent = $estimatedTokenSavingsPercent
        selected_quality_gain_units = $selectedQualityGain
        selected_critical_path_gain_units = $selectedCriticalPathGain
        selected_control_gain_units = $selectedControlGain
        selected_organization_value_units = $selectedOrganizationValue
        decomposition_difficulty_savings_units = $decompositionDifficultySavings
        context_packet_overhead_units = $contextPacketTotal
        integration_overhead_units = $integrationOverheadTotal
        expected_single_agent_rework_units = $expectedReworkUnits
        expected_rework_avoidance_units = $appliedReworkAvoidance
        independent_assurance_cost_units = $appliedVerificationWeight
        recommended_children = $recommendedChildren
        ceiling_not_target = $true
        maximum_active_agents_including_existing = $activeNow + $recommendedChildren
        worker_children = $workerCount
        verifier_children = $verifierCount
        delegated_workstreams = @($delegated | ForEach-Object { $_.id })
        lead_or_queued_workstreams = @($leadItems | ForEach-Object { $_.id })
        eligible_independent_workstreams = $potentialCandidates.Count
        token_efficient_delegation_workstreams = $tokenEfficientCandidates.Count
        organizationally_valuable_workstreams = $candidates.Count
        free_child_slots_observed = $freeChildSlots
        physical_free_child_slots = $physicalFreeChildSlots
        runtime_snapshot_authoritative = $snapshotAuthoritative
        runtime_snapshot_source = $snapshotSource
        runtime_active_agents = @($activeAgents)
        default_descendant_spawn_quota = 0
        replan_descendant_rule = "A mission child may receive spawn quota only after it exposes at least two substantive independent substreams and the control plane reruns this planner against current runtime state."
        agent_allocations = @($allocations)
        replan_triggers = @(
            "human changes goal or design decision",
            "task graph gains or loses a workstream",
            "child completes, blocks, or duplicates work",
            "assurance discovers material follow-up",
            "runtime capacity changes",
            "coordination overhead exceeds marginal value"
        )
        reasons = @($reasons)
    }
    $result | ConvertTo-Json -Depth 12
    exit 0
}
catch {
    [ordered]@{
        valid = $false
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 4
    exit 2
}
