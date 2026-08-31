param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$companyPolicyVersion = "company-v5"
$plannerVersion = "studio-portfolio-v2"
$portfolioStates = @("opportunity", "discovery", "funded", "build", "operate", "scale", "pause", "retire")
$founderStatuses = @("not-required", "raw", "framed", "explored", "decision-ready", "authorized")
$capabilityStatuses = @("candidate", "validated", "degraded", "retired")
$assetStates = @("operate", "scale", "pause", "retire")
$evidenceClasses = @("external-outcome", "production-observation", "controlled-experiment", "executable-test", "source-analysis", "agent-claim")
$envelopeKeys = @("investment_units", "human_attention_units", "maintenance_units", "risk_capacity_units")
$activeInvestmentStates = @("funded", "build", "scale")
$allowedTransitions = @{
    opportunity = @("opportunity", "discovery", "pause", "retire")
    discovery = @("discovery", "funded", "pause", "retire")
    funded = @("funded", "discovery", "build", "pause", "retire")
    build = @("build", "discovery", "operate", "pause", "retire")
    operate = @("operate", "scale", "pause", "retire")
    scale = @("scale", "operate", "pause", "retire")
    pause = @("pause", "discovery", "funded", "build", "operate", "retire")
    retire = @("retire")
}

function Get-Value {
    param($Object, [string]$Name, $Default)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        if ($Default -is [System.Array]) { return ,$Default }
        return $Default
    }
    if ($property.Value -is [System.Array]) { return ,$property.Value }
    return $property.Value
}

function Get-StrictBool {
    param($Value, [string]$Name)
    if ($Value -isnot [bool]) { throw "$Name must be a boolean" }
    return $Value
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

function Get-NonEmptyString {
    param($Value, [string]$Name)
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)) {
        throw "$Name must be a non-empty string"
    }
    return $Value.Trim()
}

function Get-OptionalString {
    param($Value, [string]$Name)
    if ($null -eq $Value) { return $null }
    return Get-NonEmptyString $Value $Name
}

function Get-IsoDate {
    param($Value, [string]$Name)
    $text = Get-NonEmptyString $Value $Name
    $parsed = [datetime]::MinValue
    $ok = [datetime]::TryParseExact(
        $text,
        "yyyy-MM-dd",
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::None,
        [ref]$parsed
    )
    if (-not $ok) { throw "$Name must use YYYY-MM-DD" }
    return $parsed.Date
}

function Get-StringArray {
    param($Value, [string]$Name, [bool]$NonEmpty = $false)
    if ($Value -isnot [System.Array]) { throw "$Name must be an array of non-empty strings" }
    $result = [System.Collections.Generic.List[string]]::new()
    $seen = @{}
    foreach ($item in @($Value)) {
        if ($item -isnot [string] -or [string]::IsNullOrWhiteSpace($item)) {
            throw "$Name must be an array of non-empty strings"
        }
        $normalized = $item.Trim()
        if ($seen.ContainsKey($normalized)) { throw "$Name must not contain duplicates" }
        $seen[$normalized] = $true
        $result.Add($normalized)
    }
    if ($NonEmpty -and $result.Count -eq 0) { throw "$Name must contain at least one item" }
    return $result.ToArray()
}

function Get-ObjectArray {
    param($Value, [string]$Name)
    if ($Value -isnot [System.Array]) { throw "$Name must be an array of objects" }
    foreach ($item in @($Value)) {
        if ($null -eq $item -or $item -isnot [pscustomobject]) {
            throw "$Name must be an array of objects"
        }
    }
    return @($Value)
}

function Get-Envelope {
    param($Value, [string]$Name)
    if ($null -eq $Value -or $Value -isnot [pscustomobject]) { throw "$Name must be an object" }
    $result = [ordered]@{}
    foreach ($key in $envelopeKeys) {
        $result[$key] = Get-BoundedInt (Get-Value $Value $key 0) "$Name.$key" 0 1000
    }
    return $result
}

function Get-IndexedObjects {
    param([array]$Values, [string]$Name)
    $result = @{}
    for ($index = 0; $index -lt $Values.Count; $index++) {
        $id = Get-NonEmptyString (Get-Value $Values[$index] "id" $null) "$Name[$index].id"
        if ($result.ContainsKey($id)) { throw "duplicate $Name id: $id" }
        $result[$id] = $Values[$index]
    }
    return $result
}

function ConvertTo-Asset {
    param([string]$AssetId, $Raw)
    $state = Get-Value $Raw "lifecycle_state" $null
    if ($assetStates -notcontains $state) { throw "asset $AssetId.lifecycle_state is not allowed" }
    $custodian = Get-OptionalString (Get-Value $Raw "custodian_agent_id" $null) "asset $AssetId.custodian_agent_id"
    $lease = Get-OptionalString (Get-Value $Raw "custody_lease_expires_at" $null) "asset $AssetId.custody_lease_expires_at"
    if (($null -ne $custodian) -ne ($null -ne $lease)) {
        throw "asset $AssetId custodian_agent_id and custody_lease_expires_at must appear together"
    }
    return [pscustomobject][ordered]@{
        id = $AssetId
        lifecycle_state = $state
        owner_seat_id = Get-NonEmptyString (Get-Value $Raw "owner_seat_id" $null) "asset $AssetId.owner_seat_id"
        custodian_agent_id = $custodian
        custody_lease_expires_at = $lease
        feedback_channel_ref = Get-NonEmptyString (Get-Value $Raw "feedback_channel_ref" $null) "asset $AssetId.feedback_channel_ref"
        observability_ref = Get-NonEmptyString (Get-Value $Raw "observability_ref" $null) "asset $AssetId.observability_ref"
        incident_route_ref = Get-NonEmptyString (Get-Value $Raw "incident_route_ref" $null) "asset $AssetId.incident_route_ref"
        safe_state_ref = Get-NonEmptyString (Get-Value $Raw "safe_state_ref" $null) "asset $AssetId.safe_state_ref"
        retirement_plan_ref = Get-NonEmptyString (Get-Value $Raw "retirement_plan_ref" $null) "asset $AssetId.retirement_plan_ref"
        maintenance_units = Get-BoundedInt (Get-Value $Raw "maintenance_units" 0) "asset $AssetId.maintenance_units" 0 1000
        evidence_fresh = Get-StrictBool (Get-Value $Raw "evidence_fresh" $null) "asset $AssetId.evidence_fresh"
        review_triggers = @(Get-StringArray (Get-Value $Raw "review_triggers" $null) "asset $AssetId.review_triggers" $true)
    }
}

function Test-Capability {
    param([string]$CapabilityId, $Raw)
    $status = Get-Value $Raw "status" $null
    if ($capabilityStatuses -notcontains $status) { throw "capability $CapabilityId.status is not allowed" }
    $evidenceCount = Get-BoundedInt (Get-Value $Raw "cross_task_evidence_count" 0) "capability $CapabilityId.cross_task_evidence_count" 0 1000
    $reviewed = Get-StrictBool (Get-Value $Raw "independent_reviewed" $false) "capability $CapabilityId.independent_reviewed"
    $evidenceRefs = @(Get-StringArray (Get-Value $Raw "evidence_refs" @()) "capability $CapabilityId.evidence_refs")
    $null = @(Get-StringArray (Get-Value $Raw "known_limitations" @()) "capability $CapabilityId.known_limitations")
    $null = Get-OptionalString (Get-Value $Raw "last_validated_at" $null) "capability $CapabilityId.last_validated_at"
    if ($status -eq "validated" -and ($evidenceCount -lt 2 -or $evidenceRefs.Count -lt 2 -or -not $reviewed)) {
        throw "capability $CapabilityId cannot be validated without two cross-task evidence records and independent review"
    }
}

function ConvertTo-RealityEvidence {
    param([string]$EvidenceId, $Raw)
    $evidenceClass = Get-Value $Raw "evidence_class" $null
    if ($evidenceClasses -notcontains $evidenceClass) { throw "reality evidence $EvidenceId.evidence_class is not allowed" }
    $null = Get-NonEmptyString (Get-Value $Raw "source_ref" $null) "reality evidence $EvidenceId.source_ref"
    $observedAt = Get-IsoDate (Get-Value $Raw "observed_at" $null) "reality evidence $EvidenceId.observed_at"
    $freshUntil = Get-IsoDate (Get-Value $Raw "fresh_until" $null) "reality evidence $EvidenceId.fresh_until"
    if ($freshUntil -lt $observedAt) { throw "reality evidence $EvidenceId.fresh_until cannot precede observed_at" }
    $null = Get-NonEmptyString (Get-Value $Raw "claim" $null) "reality evidence $EvidenceId.claim"
    $producerControlsSource = Get-StrictBool (Get-Value $Raw "producer_controls_source" $false) "reality evidence $EvidenceId.producer_controls_source"
    $confidence = Get-BoundedInt (Get-Value $Raw "confidence" 0) "reality evidence $EvidenceId.confidence" 0 5
    return [pscustomobject]@{
        evidence_class = $evidenceClass
        observed_at = $observedAt
        fresh_until = $freshUntil
        producer_controls_source = $producerControlsSource
        confidence = $confidence
    }
}

function ConvertTo-PortfolioItem {
    param([string]$ItemId, $Raw, [hashtable]$Assets)
    $state = Get-Value $Raw "current_state" $null
    if ($portfolioStates -notcontains $state) { throw "$ItemId.current_state is not allowed" }
    $previous = Get-Value $Raw "previous_state" $null
    if ($null -ne $previous) {
        if ($portfolioStates -notcontains $previous) { throw "$ItemId.previous_state is not allowed" }
        if ($allowedTransitions[$previous] -notcontains $state) { throw "$ItemId transition $previous -> $state is not allowed" }
    }
    $founderStatus = Get-Value $Raw "founder_charter_status" "not-required"
    if ($founderStatuses -notcontains $founderStatus) { throw "$ItemId.founder_charter_status is not allowed" }
    $founderRef = Get-OptionalString (Get-Value $Raw "founder_charter_ref" $null) "$ItemId.founder_charter_ref"
    if ($founderStatus -ne "not-required" -and $null -eq $founderRef) { throw "$ItemId.founder_charter_ref is required for a Founder-governed item" }
    if ($state -eq "build" -and $founderStatus -ne "authorized") { throw "$ItemId cannot be in build before Founder Charter authorization" }
    $assetId = Get-OptionalString (Get-Value $Raw "asset_id" $null) "$ItemId.asset_id"
    if ($state -in @("operate", "scale", "pause") -and ($null -eq $assetId -or -not $Assets.ContainsKey($assetId))) {
        throw "$ItemId in $state requires an existing product asset"
    }
    if ($null -ne $assetId -and -not $Assets.ContainsKey($assetId)) { throw "$ItemId.asset_id does not exist" }

    $result = [pscustomobject][ordered]@{
        id = $ItemId
        title = Get-NonEmptyString (Get-Value $Raw "title" $null) "$ItemId.title"
        current_state = $state
        previous_state = $previous
        founder_charter_status = $founderStatus
        founder_charter_ref = $founderRef
        mandatory_human_gate = Get-StrictBool (Get-Value $Raw "mandatory_human_gate" $false) "$ItemId.mandatory_human_gate"
        stop_condition_triggered = Get-StrictBool (Get-Value $Raw "stop_condition_triggered" $false) "$ItemId.stop_condition_triggered"
        evidence_fresh = Get-StrictBool (Get-Value $Raw "evidence_fresh" $false) "$ItemId.evidence_fresh"
        owner_seat_id = Get-NonEmptyString (Get-Value $Raw "owner_seat_id" $null) "$ItemId.owner_seat_id"
        asset_id = $assetId
        strategic_alignment = Get-BoundedInt (Get-Value $Raw "strategic_alignment" 0) "$ItemId.strategic_alignment" 0 5
        user_evidence = Get-BoundedInt (Get-Value $Raw "user_evidence" 0) "$ItemId.user_evidence" 0 5
        outcome_evidence = Get-BoundedInt (Get-Value $Raw "outcome_evidence" 0) "$ItemId.outcome_evidence" 0 5
        urgency = Get-BoundedInt (Get-Value $Raw "urgency" 0) "$ItemId.urgency" 0 5
        option_value = Get-BoundedInt (Get-Value $Raw "option_value" 0) "$ItemId.option_value" 0 5
        confidence = Get-BoundedInt (Get-Value $Raw "confidence" 0) "$ItemId.confidence" 0 5
        risk = Get-BoundedInt (Get-Value $Raw "risk" 0) "$ItemId.risk" 0 5
        reversibility = Get-BoundedInt (Get-Value $Raw "reversibility" 0) "$ItemId.reversibility" 0 5
        investment_units = Get-BoundedInt (Get-Value $Raw "investment_units" 0) "$ItemId.investment_units" 0 1000
        human_attention_units = Get-BoundedInt (Get-Value $Raw "human_attention_units" 0) "$ItemId.human_attention_units" 0 1000
        maintenance_units = Get-BoundedInt (Get-Value $Raw "maintenance_units" 0) "$ItemId.maintenance_units" 0 1000
        risk_capacity_units = Get-BoundedInt (Get-Value $Raw "risk_capacity_units" 0) "$ItemId.risk_capacity_units" 0 1000
        reality_evidence_refs = @(Get-StringArray (Get-Value $Raw "reality_evidence_refs" @()) "$ItemId.reality_evidence_refs")
        stop_conditions = @(Get-StringArray (Get-Value $Raw "stop_conditions" $null) "$ItemId.stop_conditions" $true)
        review_triggers = @(Get-StringArray (Get-Value $Raw "review_triggers" $null) "$ItemId.review_triggers" $true)
        next_evidence_action = Get-NonEmptyString (Get-Value $Raw "next_evidence_action" $null) "$ItemId.next_evidence_action"
    }
    if ($state -eq "scale" -and (-not $result.evidence_fresh -or $result.outcome_evidence -lt 4 -or $result.reality_evidence_refs.Count -eq 0)) {
        throw "$ItemId cannot be in scale without fresh externally grounded outcome evidence"
    }
    return $result
}

function Get-PriorityScore {
    param($Item)
    return [int](
        4 * $Item.strategic_alignment +
        3 * $Item.user_evidence +
        4 * $Item.outcome_evidence +
        2 * $Item.urgency +
        2 * $Item.option_value +
        $Item.confidence +
        2 * $Item.reversibility -
        3 * $Item.risk -
        $Item.investment_units -
        2 * $Item.maintenance_units -
        2 * $Item.human_attention_units
    )
}

function Get-BaseDecision {
    param($Item)
    $state = $Item.current_state
    if ($state -eq "retire") { return [pscustomobject]@{ action = "retain-retired"; next = "retire"; fixed = $true; reasons = @("Retired work is not silently resurrected.") } }
    if ($Item.mandatory_human_gate) { return [pscustomobject]@{ action = "human-gated"; next = $state; fixed = $true; reasons = @("A mandatory human gate is unresolved.") } }
    if ($Item.stop_condition_triggered) {
        if ($state -eq "pause") { return [pscustomobject]@{ action = "retire-review"; next = "pause"; fixed = $true; reasons = @("A stop condition remains triggered while paused.") } }
        return [pscustomobject]@{ action = "pause"; next = "pause"; fixed = $true; reasons = @("A recorded stop condition is triggered.") }
    }
    if ($state -in @("operate", "scale") -and -not $Item.evidence_fresh) { return [pscustomobject]@{ action = "revalidate"; next = $state; fixed = $true; reasons = @("Operating evidence is stale.") } }
    if ($state -eq "operate") {
        if ($Item.outcome_evidence -le 1 -and $Item.reality_evidence_refs.Count -gt 0) { return [pscustomobject]@{ action = "pause"; next = "pause"; fixed = $true; reasons = @("Fresh reality evidence shows weak outcome.") } }
        if ($Item.outcome_evidence -ge 4 -and $Item.user_evidence -ge 3 -and $Item.risk -le 2 -and $Item.has_qualifying_external_outcome) { return [pscustomobject]@{ action = "scale-candidate"; next = "scale"; fixed = $false; reasons = @("Fresh operating evidence supports a scale review.") } }
        return [pscustomobject]@{ action = "continue"; next = "operate"; fixed = $true; reasons = @("Continue bounded operation and observation.") }
    }
    if ($state -eq "scale") {
        if ($Item.outcome_evidence -lt 3 -or $Item.risk -ge 4) { return [pscustomobject]@{ action = "pause"; next = "pause"; fixed = $true; reasons = @("Scale evidence or risk no longer supports expansion.") } }
        return [pscustomobject]@{ action = "continue"; next = "scale"; fixed = $true; reasons = @("Continue the current scale horizon.") }
    }
    if ($state -eq "pause") {
        if ($Item.evidence_fresh -and $Item.founder_charter_status -eq "authorized") { return [pscustomobject]@{ action = "resume-review"; next = "pause"; fixed = $true; reasons = @("Fresh evidence permits a governed resume review.") } }
        return [pscustomobject]@{ action = "revalidate"; next = "pause"; fixed = $true; reasons = @("Paused work needs fresh evidence before resumption.") }
    }
    if ($state -in @("funded", "build")) {
        if (-not $Item.evidence_fresh) { return [pscustomobject]@{ action = "revalidate"; next = $state; fixed = $true; reasons = @("Investment evidence is stale.") } }
        return [pscustomobject]@{ action = "continue"; next = $state; fixed = $true; reasons = @("Continue only to the current funded milestone.") }
    }
    if ($state -eq "opportunity" -and $Item.founder_charter_status -eq "authorized") {
        return [pscustomobject]@{ action = "discover"; next = "discovery"; fixed = $true; reasons = @("An authorized opportunity must enter bounded discovery before funding comparison.") }
    }
    if ($Item.founder_charter_status -ne "authorized") {
        if ($Item.strategic_alignment -le 1 -and $Item.user_evidence -le 1 -and $Item.option_value -le 1) { return [pscustomobject]@{ action = "reject"; next = "retire"; fixed = $true; reasons = @("Weak strategic, user, and option-value evidence does not justify discovery.") } }
        return [pscustomobject]@{ action = "discover"; next = "discovery"; fixed = $true; reasons = @("Founder intent is not authorized; only reversible discovery may proceed.") }
    }
    if ($Item.user_evidence -lt 2 -and $Item.option_value -lt 4) { return [pscustomobject]@{ action = "discover"; next = "discovery"; fixed = $true; reasons = @("Evidence is too weak for investment; run the next reversible evidence action.") } }
    return [pscustomobject]@{ action = "fund-candidate"; next = "funded"; fixed = $false; reasons = @("The item is eligible for bounded portfolio comparison.") }
}

try {
    $data = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
    if ($null -eq $data -or $data -isnot [pscustomobject]) { throw "studio state must be a JSON object" }
    $studioId = Get-NonEmptyString (Get-Value $data "studio_id" $null) "studio_id"
    if ((Get-Value $data "company_policy_version" $null) -ne $companyPolicyVersion) { throw "company_policy_version must be $companyPolicyVersion" }
    $asOf = Get-IsoDate (Get-Value $data "as_of" $null) "as_of"
    $activeLimit = Get-BoundedInt (Get-Value $data "portfolio_active_limit" 1) "portfolio_active_limit" 0 256
    $totalEnvelope = Get-Envelope (Get-Value $data "investment_envelope" $null) "investment_envelope"
    $reserved = Get-Envelope (Get-Value $data "reserved_envelope" $null) "reserved_envelope"
    $available = [ordered]@{}
    foreach ($key in $envelopeKeys) {
        if ($reserved[$key] -gt $totalEnvelope[$key]) { throw "reserved_envelope.$key exceeds investment_envelope.$key" }
        $available[$key] = $totalEnvelope[$key] - $reserved[$key]
    }

    $rawAssets = Get-IndexedObjects @(Get-ObjectArray (Get-Value $data "product_assets" @()) "product_assets") "product_assets"
    $assets = @{}
    foreach ($assetId in $rawAssets.Keys) { $assets[$assetId] = ConvertTo-Asset $assetId $rawAssets[$assetId] }
    $rawEvidence = Get-IndexedObjects @(Get-ObjectArray (Get-Value $data "reality_evidence" @()) "reality_evidence") "reality_evidence"
    $evidence = @{}
    foreach ($evidenceId in $rawEvidence.Keys) { $evidence[$evidenceId] = ConvertTo-RealityEvidence $evidenceId $rawEvidence[$evidenceId] }
    $rawCapabilities = Get-IndexedObjects @(Get-ObjectArray (Get-Value $data "capabilities" @()) "capabilities") "capabilities"
    foreach ($capabilityId in $rawCapabilities.Keys) { Test-Capability $capabilityId $rawCapabilities[$capabilityId] }
    $null = @(Get-ObjectArray (Get-Value $data "decision_history" @()) "decision_history")

    $rawItems = Get-IndexedObjects @(Get-ObjectArray (Get-Value $data "portfolio_items" @()) "portfolio_items") "portfolio_items"
    $items = @()
    foreach ($itemId in @($rawItems.Keys | Sort-Object)) {
        $item = ConvertTo-PortfolioItem $itemId $rawItems[$itemId] $assets
        $missing = @($item.reality_evidence_refs | Where-Object { -not $rawEvidence.ContainsKey($_) } | Sort-Object)
        if ($missing.Count -gt 0) { throw "$itemId references missing reality evidence: $($missing -join ', ')" }
        $derivedFreshness = $false
        $hasQualifyingExternalOutcome = $false
        foreach ($evidenceRef in $item.reality_evidence_refs) {
            $record = $evidence[$evidenceRef]
            $recordIsFresh = $record.observed_at -le $asOf -and $asOf -le $record.fresh_until
            if ($recordIsFresh) { $derivedFreshness = $true }
            if (
                $record.evidence_class -in @("external-outcome", "production-observation") -and
                -not $record.producer_controls_source -and
                $recordIsFresh -and
                $record.confidence -ge 3
            ) { $hasQualifyingExternalOutcome = $true }
        }
        if ($item.evidence_fresh -ne $derivedFreshness) {
            throw "$itemId.evidence_fresh conflicts with evidence dates as of $($asOf.ToString('yyyy-MM-dd'))"
        }
        $item | Add-Member -NotePropertyName has_qualifying_external_outcome -NotePropertyValue $hasQualifyingExternalOutcome
        if ($item.current_state -eq "scale" -and -not $item.has_qualifying_external_outcome) {
            throw "$itemId cannot scale without fresh non-producer-controlled outcome evidence"
        }
        if ($null -ne $item.asset_id) {
            $asset = $assets[$item.asset_id]
            if ($item.current_state -in @("operate", "scale") -and $asset.lifecycle_state -notin @("operate", "scale")) { throw "$itemId state conflicts with product asset lifecycle_state" }
            if ($item.current_state -eq "scale" -and -not $asset.evidence_fresh) { throw "$itemId cannot scale with stale product asset evidence" }
        }
        $items += $item
    }

    $activeCount = @($items | Where-Object { $activeInvestmentStates -contains $_.current_state }).Count
    $freeSlots = [math]::Max(0, $activeLimit - $activeCount)
    $decisions = @()
    $candidates = @()
    foreach ($item in $items) {
        $base = Get-BaseDecision $item
        $score = Get-PriorityScore $item
        if ($base.fixed) {
            $decisions += [pscustomobject][ordered]@{
                id = $item.id; current_state = $item.current_state; recommended_action = $base.action
                recommended_next_state = $base.next; priority_score = $score; hard_gate_or_obligation = $true
                reasons = @($base.reasons); next_evidence_action = $item.next_evidence_action
            }
        }
        else {
            $candidates += [pscustomobject]@{ score = $score; item = $item; action = $base.action; next = $base.next; reasons = @($base.reasons) }
        }
    }
    $candidates = @($candidates | Sort-Object -Property @{Expression = "score"; Descending = $true}, @{Expression = { $_.item.id }; Descending = $false})
    $selected = @()
    $queued = @()
    $used = [ordered]@{}
    foreach ($key in $envelopeKeys) { $used[$key] = 0 }
    foreach ($candidate in $candidates) {
        $item = $candidate.item
        $fits = $true
        foreach ($key in $envelopeKeys) { if ($used[$key] + $item.$key -gt $available[$key]) { $fits = $false } }
        $reasons = @($candidate.reasons)
        if ($candidate.score -le 0) {
            if ($item.current_state -eq "operate") { $finalAction = "continue"; $finalState = "operate" }
            else { $finalAction = "discover"; $finalState = "discovery" }
            $reasons += "Estimated marginal organizational value does not justify this investment horizon."
        }
        elseif ($freeSlots -le 0 -or -not $fits) {
            $finalAction = "queue"; $finalState = $item.current_state; $queued += $item.id
            $reasons += "The active-project limit or available investment envelope is binding."
        }
        else {
            if ($candidate.action -eq "fund-candidate") { $finalAction = "fund" } else { $finalAction = "scale" }
            $finalState = $candidate.next
            $freeSlots -= 1
            foreach ($key in $envelopeKeys) { $used[$key] += $item.$key }
            $selected += $item.id
        }
        $decisions += [pscustomobject][ordered]@{
            id = $item.id; current_state = $item.current_state; recommended_action = $finalAction
            recommended_next_state = $finalState; priority_score = $candidate.score; hard_gate_or_obligation = $false
            reasons = @($reasons); next_evidence_action = $item.next_evidence_action
        }
    }

    foreach ($decision in $decisions) {
        if ($allowedTransitions[$decision.current_state] -notcontains $decision.recommended_next_state) {
            throw "planner produced illegal transition for $($decision.id): $($decision.current_state) -> $($decision.recommended_next_state)"
        }
    }

    [ordered]@{
        valid = $true
        machine_selected = $true
        studio_id = $studioId
        company_policy_version = $companyPolicyVersion
        planner_version = $plannerVersion
        transition_closed = $true
        estimate_not_measured = $true
        portfolio_active_limit = $activeLimit
        current_active_investments = $activeCount
        available_envelope = $available
        selected_incremental_envelope = $used
        selected_new_investments = @($selected)
        queued_investments = @($queued)
        recommendations = @($decisions | Sort-Object id)
        control_note = "Recommendations do not bypass Founder, human, permission, runtime, release, or external-effect gates. Record the accountable decision and update persistent studio state after approval."
    } | ConvertTo-Json -Depth 12
    exit 0
}
catch {
    [ordered]@{ valid = $false; error = $_.Exception.Message } | ConvertTo-Json -Depth 4
    exit 2
}
