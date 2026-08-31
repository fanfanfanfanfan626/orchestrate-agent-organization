param(
    [Parameter(Mandatory = $true, Position = 0)] [string]$InputPath,
    [Parameter(Mandatory = $true, Position = 1)] [string]$ManifestPath,
    [Parameter(Mandatory = $true, Position = 2)] [string]$ExpectedManifestSha
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$packetVersion = "integration-v2"
$manifestVersion = "assurance-v1"
$severities = @("P0", "P1", "P2")
$obligationStatuses = @("open-blocker", "contested-blocker", "verified-closed")
$safeActions = @("hold", "pause", "discovery", "revalidate", "operate-safe", "human-gated", "retire-review", "retire")
$advanceActions = @("resume", "release", "scale", "cutover")
$subjectKinds = @("product-asset", "live-investment", "external-paused-product")
$riskLevels = @("low", "medium", "high", "critical")
$controlStatuses = @("verified", "declared-unverified", "proposed", "missing-blocker", "not-applicable")
$controlFields = @("durable_owner", "on_call", "reconciliation", "support_surface", "slis_alerts", "incident_safe_state", "maintenance", "retirement", "next_evidence_trigger")
$mandatoryHighRiskControls = @("durable_owner", "on_call", "slis_alerts", "incident_safe_state", "maintenance", "retirement", "next_evidence_trigger")
$gateAuthorities = @("human", "machine", "external")
$gateStatuses = @("required", "satisfied")
$evidenceResults = @("pass", "fail")
$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

function Add-ValidationError { param([string]$Message) $script:errors.Add($Message) }
function Test-Ordinal {
    param($Left, $Right)
    if ($null -eq $Left -or $null -eq $Right) { return $null -eq $Left -and $null -eq $Right }
    return [string]::Equals([string]$Left, [string]$Right, [System.StringComparison]::Ordinal)
}
function Test-InSet {
    param([string]$Value, [string[]]$Allowed)
    foreach ($item in $Allowed) { if (Test-Ordinal $Value $item) { return $true } }
    return $false
}
function New-OrdinalDictionary { return ,[System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal) }
function New-OrdinalSet { return ,[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal) }
function Get-Value {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $properties=@($Object.PSObject.Properties|Where-Object{Test-Ordinal $_.Name $Name})
    if ($properties.Count-ne1) { return $null }
    $property=$properties[0]
    if ($property.Value -is [System.Array]) { return ,$property.Value }
    return $property.Value
}
function Test-NonEmptyString { param($Value) return $Value -is [string] -and -not [string]::IsNullOrWhiteSpace($Value) }
function Require-String {
    param($Object, [string]$Name, [string]$Label)
    $value = Get-Value $Object $Name
    if (-not (Test-NonEmptyString $value)) { Add-ValidationError "$Label.$Name must be a non-empty string"; return "" }
    return $value.Trim()
}
function Optional-String {
    param($Object, [string]$Name, [string]$Label)
    $value = Get-Value $Object $Name
    if ($null -eq $value) { return $null }
    if (-not (Test-NonEmptyString $value)) { Add-ValidationError "$Label.$Name must be null or a non-empty string"; return $null }
    return $value.Trim()
}
function Require-Bool {
    param($Object, [string]$Name, [string]$Label)
    $value = Get-Value $Object $Name
    if ($value -isnot [bool]) { Add-ValidationError "$Label.$Name must be a JSON Boolean"; return $false }
    return [bool]$value
}
function Get-ObjectArray {
    param($Value, [string]$Label)
    if ($Value -isnot [System.Array]) { Add-ValidationError "$Label must be an array of objects"; return }
    foreach ($item in @($Value)) {
        if ($null -eq $item -or $item -is [string] -or $item -is [ValueType] -or $item -is [System.Array]) { Add-ValidationError "$Label must be an array of objects"; return }
    }
    foreach ($item in @($Value)) { Write-Output $item }
}
function Get-StringArray {
    param($Value, [string]$Label, [bool]$AllowEmpty = $true)
    if ($Value -isnot [System.Array]) { Add-ValidationError "$Label must be an array of non-empty strings"; return }
    $result = [System.Collections.Generic.List[string]]::new()
    $seen = New-OrdinalSet
    foreach ($item in @($Value)) {
        if (-not (Test-NonEmptyString $item)) { Add-ValidationError "$Label must be an array of non-empty strings"; return }
        $normalized = $item.Trim()
        if (-not $seen.Add($normalized)) { Add-ValidationError "$Label must not contain duplicates" }
        $result.Add($normalized)
    }
    if (-not $AllowEmpty -and $result.Count -eq 0) { Add-ValidationError "$Label must not be empty" }
    foreach ($item in $result) { Write-Output $item }
}
function Test-StringArrayEqual {
    param([object[]]$Left, [object[]]$Right)
    if (@($Left).Count -ne @($Right).Count) { return $false }
    for ($i = 0; $i -lt @($Left).Count; $i++) { if (-not (Test-Ordinal $Left[$i] $Right[$i])) { return $false } }
    return $true
}
function Require-Enum { param([string]$Value, [string[]]$Allowed, [string]$Label) if ($Value -and -not (Test-InSet $Value $Allowed)) { Add-ValidationError "$Label is not allowed" } }
function Require-Sha { param([string]$Value, [string]$Label) if ($Value -and $Value -cnotmatch '^[0-9a-f]{64}$') { Add-ValidationError "$Label must be a lowercase SHA-256 digest" } }
function Parse-IsoDate {
    param([string]$Value, [string]$Label)
    $parsed = [datetime]::MinValue
    $ok = [datetime]::TryParseExact($Value, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::None, [ref]$parsed)
    if (-not $ok) { Add-ValidationError "$Label must be an ISO date"; return $null }
    return $parsed
}
function Test-SameKeys {
    param($Left, $Right)
    if ($Left.Count -ne $Right.Count) { return $false }
    foreach ($key in $Left.Keys) { if (-not $Right.ContainsKey($key)) { return $false } }
    return $true
}
function Test-ExactControlKeys {
    param($Controls, [string]$Label)
    $actual = New-OrdinalSet
    foreach ($property in $Controls.PSObject.Properties) { [void]$actual.Add($property.Name) }
    foreach ($field in $script:controlFields) { if (-not $actual.Contains($field)) { Add-ValidationError "$Label is missing $field" } }
    foreach ($field in $actual) { if (-not (Test-InSet $field $script:controlFields)) { Add-ValidationError "$Label has unexpected field $field" } }
}
function Test-ExactObjectKeys {
    param($Object,[string[]]$Expected,[string]$Label)
    $actual=New-OrdinalSet;foreach($property in $Object.PSObject.Properties){[void]$actual.Add($property.Name)}
    foreach($field in @($Expected|Sort-Object -CaseSensitive)){if(-not$actual.Contains($field)){Add-ValidationError "$Label is missing $field"}}
    foreach($field in @($actual|Sort-Object -CaseSensitive)){if(-not(Test-InSet $field $Expected)){Add-ValidationError "$Label has unexpected field $field"}}
}
function Get-FileShaLower { param([string]$Path) return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
function Test-BoundEvidenceFile {
    param([string]$Reference,[string]$ExpectedSha,[string]$Label,[string]$ManifestFile)
    if ([System.IO.Path]::IsPathRooted($Reference) -or @($Reference -split '[\\/]').Contains("..")) {
        Add-ValidationError "$Label must be a relative path inside the manifest directory"
        return $null
    }
    $root=[System.IO.Path]::GetFullPath((Split-Path -Parent $ManifestFile));$candidate=[System.IO.Path]::GetFullPath((Join-Path $root $Reference));$prefix=$root.TrimEnd([System.IO.Path]::DirectorySeparatorChar,[System.IO.Path]::AltDirectorySeparatorChar)+[System.IO.Path]::DirectorySeparatorChar
    if(-not$candidate.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)) { Add-ValidationError "$Label must be a relative path inside the manifest directory";return $null }
    $cursor=$root;foreach($part in @($Reference-split '[\\/]')){$cursor=Join-Path $cursor $part;if(Test-Path -LiteralPath $cursor){$item=Get-Item -LiteralPath $cursor -Force;if(($item.Attributes-band[System.IO.FileAttributes]::ReparsePoint)-ne0){Add-ValidationError "$Label must not traverse reparse points";return $null}}}
    if(-not(Test-Path -LiteralPath $candidate -PathType Leaf)) { Add-ValidationError "$Label file is missing or is not a regular file";return $null }
    if($ExpectedSha-and-not(Test-Ordinal (Get-FileShaLower $candidate) $ExpectedSha)){Add-ValidationError "$Label SHA-256 does not match the referenced file";return $null}
    return $candidate
}
function Test-Attestation {
    param([string]$Path,$Record,[string]$DecisionId,[string]$Label)
    if(-not(Test-NonEmptyString $Path)){return}
    try{$raw=Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}catch{Add-ValidationError "$Label must be valid JSON";return}
    if($null-eq$raw-or$raw-is[string]-or$raw-is[ValueType]-or$raw-is[System.Array]){Add-ValidationError "$Label must be a JSON object";return}
    $expected=[ordered]@{schema_version="evidence-attestation-v1";evidence_id=$Record.id;decision_id=$DecisionId;subject_id=$Record.subject_id;evidence_key=$Record.evidence_key;scope=$Record.scope;decision_version=$Record.decision_version;check_result=$Record.check_result;verified_by=$Record.verified_by;observed_at=$Record.observed_at;fresh_until=$Record.fresh_until}
    $actual=New-OrdinalSet;foreach($property in $raw.PSObject.Properties){[void]$actual.Add($property.Name)}
    foreach($field in @($expected.Keys|Sort-Object -CaseSensitive)){if(-not$actual.Contains($field)){Add-ValidationError "$Label is missing $field"}}
    foreach($field in @($actual|Sort-Object -CaseSensitive)){if(-not$expected.Contains($field)){Add-ValidationError "$Label has unexpected field $field"}}
    foreach($field in $expected.Keys){if(-not(Test-Ordinal (Get-Value $raw $field) $expected[$field])){Add-ValidationError "$Label.$field does not match its evidence record"}}
}

function Build-ManifestContext {
    param($Raw, [string]$Sha, [string]$ManifestFile)
    if ($null -eq $Raw -or $Raw -is [string] -or $Raw -is [ValueType] -or $Raw -is [System.Array]) { Add-ValidationError "manifest must be a JSON object"; return @{} }
    if (-not (Test-Ordinal (Get-Value $Raw "schema_version") $script:manifestVersion)) { Add-ValidationError "manifest.schema_version must equal $script:manifestVersion" }
    Test-ExactObjectKeys $Raw @("schema_version","manifest_id","decision_id","as_of","authorized_verifiers","findings","required_subjects","evidence_catalog") "manifest"
    $manifestId = Require-String $Raw "manifest_id" "manifest"
    $decisionId = Require-String $Raw "decision_id" "manifest"
    $asOfText = Require-String $Raw "as_of" "manifest"
    $asOf = if ($asOfText) { Parse-IsoDate $asOfText "manifest.as_of" } else { $null }
    if($null-ne$asOf-and$asOf-gt[datetime]::Today){Add-ValidationError "manifest.as_of must not be in the future"}
    $authorized = @(Get-StringArray (Get-Value $Raw "authorized_verifiers") "manifest.authorized_verifiers" $false)
    $findings = @(Get-ObjectArray (Get-Value $Raw "findings") "manifest.findings")
    $subjects = @(Get-ObjectArray (Get-Value $Raw "required_subjects") "manifest.required_subjects")
    $evidence = @(Get-ObjectArray (Get-Value $Raw "evidence_catalog") "manifest.evidence_catalog")
    $findingMap = New-OrdinalDictionary
    for ($index = 0; $index -lt $findings.Count; $index++) {
        $finding = $findings[$index]; $label = "manifest.findings[$index]"
        Test-ExactObjectKeys $finding @("id","severity","subject_id","statement","required_action","required_evidence_keys","required_gate_ids") $label
        $id = Require-String $finding "id" $label; $severity = Require-String $finding "severity" $label; $subjectId = Require-String $finding "subject_id" $label
        $statement = Require-String $finding "statement" $label; $requiredAction = Require-String $finding "required_action" $label
        $evidenceKeys = @(Get-StringArray (Get-Value $finding "required_evidence_keys") "$label.required_evidence_keys" $false)
        $gateIds = @(Get-StringArray (Get-Value $finding "required_gate_ids") "$label.required_gate_ids")
        Require-Enum $severity $script:severities "$label.severity"
        if ($id) {
            if ($findingMap.ContainsKey($id)) { Add-ValidationError "manifest finding id $id is duplicated" }
            $findingMap[$id] = @{ severity=$severity; subject_id=$subjectId; statement=$statement; required_action=$requiredAction; required_evidence_keys=$evidenceKeys; required_gate_ids=$gateIds }
        }
    }
    $subjectMap = New-OrdinalDictionary; $gateMap = New-OrdinalDictionary
    for ($index = 0; $index -lt $subjects.Count; $index++) {
        $subject = $subjects[$index]; $label = "manifest.required_subjects[$index]"
        Test-ExactObjectKeys $subject @("subject_id","subject_kind","risk_level","current_state","money_affected","accountable_owner_principal_id","required_safe_action","allowed_not_applicable","required_authority_gates") $label
        $subjectId = Require-String $subject "subject_id" $label; $subjectKind = Require-String $subject "subject_kind" $label; $riskLevel = Require-String $subject "risk_level" $label
        $currentState = Require-String $subject "current_state" $label; $moneyAffected = Require-Bool $subject "money_affected" $label; $ownerPrincipal=Require-String $subject "accountable_owner_principal_id" $label; $safeAction = Require-String $subject "required_safe_action" $label
        $allowedNa = @(Get-StringArray (Get-Value $subject "allowed_not_applicable") "$label.allowed_not_applicable")
        $gates = @(Get-ObjectArray (Get-Value $subject "required_authority_gates") "$label.required_authority_gates")
        Require-Enum $subjectKind $script:subjectKinds "$label.subject_kind"; Require-Enum $riskLevel $script:riskLevels "$label.risk_level"; Require-Enum $safeAction $script:safeActions "$label.required_safe_action"
        foreach ($field in $allowedNa) {
            if (-not (Test-InSet $field $script:controlFields)) { Add-ValidationError "$label.allowed_not_applicable contains $field" }
            if ((Test-Ordinal $field "reconciliation") -and $moneyAffected) { Add-ValidationError "$label.reconciliation cannot be not-applicable when money is affected" }
        }
        if ($subjectId) {
            if ($subjectMap.ContainsKey($subjectId)) { Add-ValidationError "manifest subject id $subjectId is duplicated" }
            $subjectMap[$subjectId] = @{ subject_kind=$subjectKind; risk_level=$riskLevel; current_state=$currentState; money_affected=$moneyAffected; accountable_owner_principal_id=$ownerPrincipal; required_safe_action=$safeAction; allowed_not_applicable=$allowedNa }
        }
        for ($gateIndex = 0; $gateIndex -lt $gates.Count; $gateIndex++) {
            $gate = $gates[$gateIndex]; $gateLabel = "$label.required_authority_gates[$gateIndex]"
            Test-ExactObjectKeys $gate @("id","action","scope","authority","decision_version") $gateLabel
            $gateId = Require-String $gate "id" $gateLabel; $action = Require-String $gate "action" $gateLabel; $scope = Require-String $gate "scope" $gateLabel
            $authority = Require-String $gate "authority" $gateLabel; $decisionVersion = Require-String $gate "decision_version" $gateLabel
            Require-Enum $action $script:advanceActions "$gateLabel.action"; Require-Enum $authority $script:gateAuthorities "$gateLabel.authority"
            if ($gateId) {
                if ($gateMap.ContainsKey($gateId)) { Add-ValidationError "manifest gate id $gateId is duplicated" }
                $gateMap[$gateId] = @{ subject_id=$subjectId; action=$action; scope=$scope; authority=$authority; decision_version=$decisionVersion }
            }
        }
    }
    foreach ($findingId in $findingMap.Keys) {
        $finding = $findingMap[$findingId]
        if (-not $subjectMap.ContainsKey($finding.subject_id)) { Add-ValidationError "manifest finding $findingId references unknown subject" }
        foreach ($gateId in $finding.required_gate_ids) {
            if (-not $gateMap.ContainsKey($gateId)) { Add-ValidationError "manifest finding $findingId references unknown gate" }
            elseif (-not (Test-Ordinal $gateMap[$gateId].subject_id $finding.subject_id)) { Add-ValidationError "manifest finding $findingId gate subject differs" }
        }
    }
    $evidenceMap = New-OrdinalDictionary
    for ($index = 0; $index -lt $evidence.Count; $index++) {
        $record = $evidence[$index]; $label = "manifest.evidence_catalog[$index]"
        Test-ExactObjectKeys $record @("id","evidence_key","subject_id","artifact_ref","artifact_sha256","check_result","scope","decision_version","observed_at","fresh_until","verified_by","attestation_ref","attestation_sha256") $label
        $id = Require-String $record "id" $label; $evidenceKey = Require-String $record "evidence_key" $label; $subjectId = Require-String $record "subject_id" $label
        $artifactRef = Require-String $record "artifact_ref" $label; $artifactSha = Require-String $record "artifact_sha256" $label; $checkResult = Require-String $record "check_result" $label
        $scope = Require-String $record "scope" $label; $decisionVersion = Require-String $record "decision_version" $label; $observedText = Require-String $record "observed_at" $label
        $freshText = Require-String $record "fresh_until" $label; $verifiedBy = Require-String $record "verified_by" $label; $attestationRef = Require-String $record "attestation_ref" $label
        $attestationSha = Require-String $record "attestation_sha256" $label
        Require-Sha $artifactSha "$label.artifact_sha256"; Require-Sha $attestationSha "$label.attestation_sha256"; Require-Enum $checkResult $script:evidenceResults "$label.check_result"
        $observed = if ($observedText) { Parse-IsoDate $observedText "$label.observed_at" } else { $null }; $fresh = if ($freshText) { Parse-IsoDate $freshText "$label.fresh_until" } else { $null }
        if ($null -ne $observed -and $null -ne $fresh -and $fresh -lt $observed) { Add-ValidationError "$label.fresh_until precedes observed_at" }
        if($null-ne$observed-and$null-ne$asOf-and$observed-gt$asOf){Add-ValidationError "$label.observed_at is after manifest.as_of"}
        if($null-ne$observed-and$observed-gt[datetime]::Today){Add-ValidationError "$label.observed_at is after validation date"}
        if ((Test-Ordinal $checkResult "pass") -and $null -ne $asOf -and $null -ne $fresh -and $fresh -lt $asOf) { Add-ValidationError "$label.passing evidence is stale at manifest.as_of" }
        if ((Test-Ordinal $checkResult "pass") -and $null -ne $fresh -and $fresh -lt [datetime]::Today) { Add-ValidationError "$label.passing evidence is stale at validation date" }
        if ($verifiedBy -and -not (Test-InSet $verifiedBy $authorized)) { Add-ValidationError "$label.verified_by is not an authorized verifier" }
        if ($subjectId -and -not $subjectMap.ContainsKey($subjectId)) { Add-ValidationError "$label.subject_id is not a required subject" }
        [void](Test-BoundEvidenceFile $artifactRef $artifactSha "$label.artifact_ref" $ManifestFile)
        $attestationPath=Test-BoundEvidenceFile $attestationRef $attestationSha "$label.attestation_ref" $ManifestFile
        Test-Attestation $attestationPath @{id=$id;subject_id=$subjectId;evidence_key=$evidenceKey;scope=$scope;decision_version=$decisionVersion;check_result=$checkResult;verified_by=$verifiedBy;observed_at=$observedText;fresh_until=$freshText} $decisionId "$label.attestation"
        if ($id) {
            if ($evidenceMap.ContainsKey($id)) { Add-ValidationError "manifest evidence id $id is duplicated" }
            $evidenceMap[$id] = @{ evidence_key=$evidenceKey; subject_id=$subjectId; artifact_ref=$artifactRef; artifact_sha256=$artifactSha; check_result=$checkResult; scope=$scope; decision_version=$decisionVersion; observed_at=$observedText; fresh_until=$freshText; verified_by=$verifiedBy; attestation_ref=$attestationRef; attestation_sha256=$attestationSha }
        }
    }
    return @{ manifest_id=$manifestId; decision_id=$decisionId; as_of=$asOfText; sha256=$Sha; authorized_verifiers=$authorized; findings=$findingMap; subjects=$subjectMap; gates=$gateMap; evidence=$evidenceMap }
}

function Get-EvidenceRefs {
    param($Value, [string]$Label, $Manifest)
    $refs = @(Get-StringArray $Value $Label)
    foreach ($ref in $refs) { if (-not $Manifest.evidence.ContainsKey($ref)) { Add-ValidationError "$Label references unknown manifest evidence $ref" } }
    foreach($ref in $refs){Write-Output $ref}
}
function Test-EvidenceCoverage {
    param([object[]]$Refs,[object[]]$RequiredKeys,[string]$SubjectId,$Manifest,[string]$Verifier=$null,[string]$Scope=$null,[string]$DecisionVersion=$null)
    $covered = New-OrdinalSet
    foreach ($ref in @($Refs)) {
        if (-not $Manifest.evidence.ContainsKey($ref)) { continue }
        $record = $Manifest.evidence[$ref]
        if (-not (Test-Ordinal $record.check_result "pass") -or -not (Test-Ordinal $record.subject_id $SubjectId)) { continue }
        if ((Test-NonEmptyString $Verifier) -and -not (Test-Ordinal $record.verified_by $Verifier)) { continue }
        if ((Test-NonEmptyString $Scope) -and -not (Test-Ordinal $record.scope $Scope)) { continue }
        if ((Test-NonEmptyString $DecisionVersion) -and -not (Test-Ordinal $record.decision_version $DecisionVersion)) { continue }
        [void]$covered.Add($record.evidence_key)
    }
    foreach ($key in @($RequiredKeys)) { if (-not $covered.Contains($key)) { return $false } }
    return $true
}
function Get-EvidenceRationale {param([object[]]$Refs)return "Verified by manifest evidence: $(@($Refs)-join ', ')"}
function Skip-JsonWhitespace {
    param([string]$Text,[ref]$Index)
    while($Index.Value-lt$Text.Length-and([char]::IsWhiteSpace($Text[$Index.Value])-or[int]$Text[$Index.Value]-eq0xFEFF)){$Index.Value++}
}
function Read-JsonStringKey {
    param([string]$Text,[ref]$Index)
    if($Index.Value-ge$Text.Length-or$Text[$Index.Value]-ne'"'){throw "invalid JSON while scanning object keys"}
    $start=$Index.Value;$Index.Value++
    while($Index.Value-lt$Text.Length){
        $char=$Text[$Index.Value]
        if($char-eq'\'){$Index.Value+=2;continue}
        if($char-eq'"'){$Index.Value++;$token=$Text.Substring($start,$Index.Value-$start);return ($token|ConvertFrom-Json)}
        $Index.Value++
    }
    throw "invalid JSON while scanning object keys"
}
function Read-JsonValueShape {
    param([string]$Text,[ref]$Index)
    Skip-JsonWhitespace $Text $Index
    if($Index.Value-ge$Text.Length){throw "invalid JSON while scanning object keys"}
    $char=$Text[$Index.Value]
    if($char-eq'{'){Read-JsonObjectShape $Text $Index;return}
    if($char-eq'['){Read-JsonArrayShape $Text $Index;return}
    if($char-eq'"'){[void](Read-JsonStringKey $Text $Index);return}
    $start=$Index.Value
    while($Index.Value-lt$Text.Length-and-not([char]::IsWhiteSpace($Text[$Index.Value]))-and$Text[$Index.Value]-notin@(',',']','}')){$Index.Value++}
    if($Index.Value-eq$start){throw "invalid JSON while scanning object keys"}
}
function Read-JsonObjectShape {
    param([string]$Text,[ref]$Index)
    $Index.Value++;$seen=New-OrdinalSet;Skip-JsonWhitespace $Text $Index
    if($Index.Value-lt$Text.Length-and$Text[$Index.Value]-eq'}'){$Index.Value++;return}
    while($true){
        Skip-JsonWhitespace $Text $Index;$key=Read-JsonStringKey $Text $Index
        if(-not$seen.Add([string]$key)){throw "duplicate JSON object key: $key"}
        Skip-JsonWhitespace $Text $Index
        if($Index.Value-ge$Text.Length-or$Text[$Index.Value]-ne':'){throw "invalid JSON while scanning object keys"}
        $Index.Value++;Read-JsonValueShape $Text $Index;Skip-JsonWhitespace $Text $Index
        if($Index.Value-ge$Text.Length){throw "invalid JSON while scanning object keys"}
        if($Text[$Index.Value]-eq'}'){$Index.Value++;return}
        if($Text[$Index.Value]-ne','){throw "invalid JSON while scanning object keys"}
        $Index.Value++
    }
}
function Read-JsonArrayShape {
    param([string]$Text,[ref]$Index)
    $Index.Value++;Skip-JsonWhitespace $Text $Index
    if($Index.Value-lt$Text.Length-and$Text[$Index.Value]-eq']'){$Index.Value++;return}
    while($true){
        Read-JsonValueShape $Text $Index;Skip-JsonWhitespace $Text $Index
        if($Index.Value-ge$Text.Length){throw "invalid JSON while scanning object keys"}
        if($Text[$Index.Value]-eq']'){$Index.Value++;return}
        if($Text[$Index.Value]-ne','){throw "invalid JSON while scanning object keys"}
        $Index.Value++
    }
}
function Assert-NoDuplicateJsonKeys {
    param([string]$Text)
    $index=0;Read-JsonValueShape $Text ([ref]$index);Skip-JsonWhitespace $Text ([ref]$index)
    if($index-ne$Text.Length){throw "invalid JSON while scanning object keys"}
}
function Get-CanonicalDelivery {
    param([string]$DecisionId,[string]$ManifestId,[string]$ManifestSha,$SubjectResults)
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("# Integration decision: $DecisionId"); $lines.Add("Manifest: $ManifestId @ sha256:$ManifestSha"); $lines.Add("")
    foreach ($subjectId in @($SubjectResults.Keys | Sort-Object -CaseSensitive)) {
        $subject = $SubjectResults[$subjectId]; $verdict = if ($subject.advancement_allowed) { "ADVANCEMENT-ALLOWED" } else { "HOLD" }
        $lines.Add("- $($subjectId): $verdict; action=$($subject.recommended_action)")
        $open = if (@($subject.open_high).Count) { @($subject.open_high) -join ", " } else { "none" }
        $controls = if (@($subject.blocking_controls).Count) { @($subject.blocking_controls) -join ", " } else { "none" }
        $gates = if (@($subject.unsatisfied_gates).Count) { @($subject.unsatisfied_gates) -join ", " } else { "none" }
        $lines.Add("  - Open P0/P1: $open"); $lines.Add("  - Blocking controls: $controls"); $lines.Add("  - Unsatisfied gates: $gates")
    }
    return ($lines -join "`n") + "`n"
}
function Get-StringShaLower {param([string]$Value)$sha=[System.Security.Cryptography.SHA256]::Create();try{$hash=$sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Value));return ([System.BitConverter]::ToString($hash)).Replace("-","").ToLowerInvariant()}finally{$sha.Dispose()}}
function Write-ResultAndExit { param($Result,[int]$Code) $Result | ConvertTo-Json -Depth 30; exit $Code }

try {
    $manifestText=Get-Content -LiteralPath $ManifestPath -Raw;Assert-NoDuplicateJsonKeys $manifestText;$manifestRaw=$manifestText|ConvertFrom-Json;$manifestSha = Get-FileShaLower $ManifestPath; $manifest = Build-ManifestContext $manifestRaw $manifestSha $ManifestPath
    $packetText=Get-Content -LiteralPath $InputPath -Raw;Assert-NoDuplicateJsonKeys $packetText;$raw=$packetText|ConvertFrom-Json
}
catch {
    $result = [ordered]@{ valid=$false; schema_version=$packetVersion; manifest_version=$manifestVersion; errors=@($_.Exception.Message); warnings=@() }
    Write-ResultAndExit $result 2
}
Require-Sha $ExpectedManifestSha "expected_manifest_sha";if(-not(Test-Ordinal $ExpectedManifestSha $manifest.sha256)){Add-ValidationError "source manifest SHA-256 does not match external trust anchor"}
if ($null -eq $raw -or $raw -is [string] -or $raw -is [ValueType] -or $raw -is [System.Array]) { Add-ValidationError "packet must be a JSON object"; $raw=[pscustomobject]@{} }
if (-not (Test-Ordinal (Get-Value $raw "schema_version") $packetVersion)) { Add-ValidationError "packet.schema_version must equal $packetVersion" }
Test-ExactObjectKeys $raw @("schema_version","decision_id","assurance_manifest","review_findings","obligations","operating_controls","authority_gates") "packet"
$decisionId = Require-String $raw "decision_id" "packet"; $binding = Get-Value $raw "assurance_manifest"
if ($null -eq $binding -or $binding -is [string] -or $binding -is [ValueType] -or $binding -is [System.Array]) { Add-ValidationError "packet.assurance_manifest must be an object"; $binding=[pscustomobject]@{} }
Test-ExactObjectKeys $binding @("id","sha256") "packet.assurance_manifest"
$bindingId=Require-String $binding "id" "packet.assurance_manifest"; $bindingSha=Require-String $binding "sha256" "packet.assurance_manifest"; Require-Sha $bindingSha "packet.assurance_manifest.sha256"
if (-not (Test-Ordinal $bindingId $manifest.manifest_id)) { Add-ValidationError "packet assurance manifest id does not match source manifest" }
if (-not (Test-Ordinal $bindingSha $manifest.sha256)) { Add-ValidationError "packet assurance manifest SHA-256 does not match source manifest" }
if (-not (Test-Ordinal $decisionId $manifest.decision_id)) { Add-ValidationError "packet decision_id does not match source manifest" }
$findings=@(Get-ObjectArray (Get-Value $raw "review_findings") "review_findings"); $obligations=@(Get-ObjectArray (Get-Value $raw "obligations") "obligations"); $controlPackets=@(Get-ObjectArray (Get-Value $raw "operating_controls") "operating_controls"); $gates=@(Get-ObjectArray (Get-Value $raw "authority_gates") "authority_gates")

$packetFindings=New-OrdinalDictionary
for($index=0;$index-lt$findings.Count;$index++){
    $finding=$findings[$index];$label="review_findings[$index]"
    Test-ExactObjectKeys $finding @("id","severity","subject_id","statement","required_action","required_evidence_keys","required_gate_ids") $label
    $id=Require-String $finding "id" $label;$severity=Require-String $finding "severity" $label;$subjectId=Require-String $finding "subject_id" $label
    $statement=Require-String $finding "statement" $label;$requiredAction=Require-String $finding "required_action" $label;$evidenceKeys=@(Get-StringArray (Get-Value $finding "required_evidence_keys") "$label.required_evidence_keys" $false);$gateIds=@(Get-StringArray (Get-Value $finding "required_gate_ids") "$label.required_gate_ids")
    Require-Enum $severity $severities "$label.severity";if($id){if($packetFindings.ContainsKey($id)){Add-ValidationError "review finding id $id is duplicated"};$packetFindings[$id]=@{severity=$severity;subject_id=$subjectId;statement=$statement;required_action=$requiredAction;required_evidence_keys=$evidenceKeys;required_gate_ids=$gateIds}}
}
if(-not(Test-SameKeys $packetFindings $manifest.findings)){Add-ValidationError "packet review finding IDs do not exactly match source manifest"}
foreach($findingId in $manifest.findings.Keys){
    if(-not$packetFindings.ContainsKey($findingId)){continue};$left=$packetFindings[$findingId];$right=$manifest.findings[$findingId]
    $same=(Test-Ordinal $left.severity $right.severity)-and(Test-Ordinal $left.subject_id $right.subject_id)-and(Test-Ordinal $left.statement $right.statement)-and(Test-Ordinal $left.required_action $right.required_action)-and(Test-StringArrayEqual $left.required_evidence_keys $right.required_evidence_keys)-and(Test-StringArrayEqual $left.required_gate_ids $right.required_gate_ids)
    if(-not$same){Add-ValidationError "review finding $findingId differs from source manifest"}
}

$packetGates=New-OrdinalDictionary
for($index=0;$index-lt$gates.Count;$index++){
    $gate=$gates[$index];$label="authority_gates[$index]";$id=Require-String $gate "id" $label;$subjectId=Require-String $gate "subject_id" $label;$action=Require-String $gate "action" $label;$scope=Require-String $gate "scope" $label;$authority=Require-String $gate "authority" $label;$decisionVersion=Require-String $gate "decision_version" $label;$status=Require-String $gate "status" $label;$refs=@(Get-EvidenceRefs (Get-Value $gate "evidence_refs") "$label.evidence_refs" $manifest);$rationale=Require-String $gate "rationale" $label
    Test-ExactObjectKeys $gate @("id","subject_id","action","scope","authority","decision_version","status","evidence_refs","rationale") $label
    Require-Enum $action $advanceActions "$label.action";Require-Enum $authority $gateAuthorities "$label.authority";Require-Enum $status $gateStatuses "$label.status"
    if($id){if($packetGates.ContainsKey($id)){Add-ValidationError "authority gate id $id is duplicated"};$packetGates[$id]=@{subject_id=$subjectId;action=$action;scope=$scope;authority=$authority;decision_version=$decisionVersion;status=$status;refs=$refs}}
    if((Test-Ordinal $status "satisfied")-and-not(Test-EvidenceCoverage $refs @("gate:$id") $subjectId $manifest $null $scope $decisionVersion)){Add-ValidationError "$label.satisfied gate lacks matching manifest evidence"}
    if((Test-Ordinal $status "satisfied")-and-not(Test-Ordinal $rationale (Get-EvidenceRationale $refs))){Add-ValidationError "$label.satisfied gate rationale is not canonical"}
    if($manifest.gates.ContainsKey($id)){$source=$manifest.gates[$id];$same=(Test-Ordinal $subjectId $source.subject_id)-and(Test-Ordinal $action $source.action)-and(Test-Ordinal $scope $source.scope)-and(Test-Ordinal $authority $source.authority)-and(Test-Ordinal $decisionVersion $source.decision_version);if(-not$same){Add-ValidationError "authority gate $id differs from source manifest"}}
}
if(-not(Test-SameKeys $packetGates $manifest.gates)){Add-ValidationError "packet authority gate IDs do not exactly match source manifest"}

$obligationMap=New-OrdinalDictionary
for($index=0;$index-lt$obligations.Count;$index++){
    $obligation=$obligations[$index];$label="obligations[$index]";Test-ExactObjectKeys $obligation @("finding_id","severity","subject_id","preserved_requirement","status","owner_principal_id","required_evidence_keys","required_gate_ids","evidence_refs","verified_by","safe_action_if_open") $label;$findingId=Require-String $obligation "finding_id" $label;$severity=Require-String $obligation "severity" $label;$subjectId=Require-String $obligation "subject_id" $label;$preserved=Require-String $obligation "preserved_requirement" $label;$status=Require-String $obligation "status" $label;$owner=Require-String $obligation "owner_principal_id" $label
    $requiredKeys=@(Get-StringArray (Get-Value $obligation "required_evidence_keys") "$label.required_evidence_keys" $false);$requiredGateIds=@(Get-StringArray (Get-Value $obligation "required_gate_ids") "$label.required_gate_ids");$refs=@(Get-EvidenceRefs (Get-Value $obligation "evidence_refs") "$label.evidence_refs" $manifest);$verifiedBy=Optional-String $obligation "verified_by" $label;$safeAction=Optional-String $obligation "safe_action_if_open" $label
    Require-Enum $severity $severities "$label.severity";Require-Enum $status $obligationStatuses "$label.status"
    if($manifest.findings.ContainsKey($findingId)){$source=$manifest.findings[$findingId];if(-not(Test-Ordinal $severity $source.severity)){Add-ValidationError "obligation $findingId changes finding severity"};if(-not(Test-Ordinal $subjectId $source.subject_id)){Add-ValidationError "obligation $findingId changes finding subject"};if(-not(Test-Ordinal $preserved $source.required_action)){Add-ValidationError "obligation $findingId changes required_action"};if(-not(Test-StringArrayEqual $requiredKeys $source.required_evidence_keys)){Add-ValidationError "obligation $findingId changes required evidence"};if(-not(Test-StringArrayEqual $requiredGateIds $source.required_gate_ids)){Add-ValidationError "obligation $findingId changes required gates"}}elseif($findingId){Add-ValidationError "obligation $findingId has no source finding"}
    if($findingId){if($obligationMap.ContainsKey($findingId)){Add-ValidationError "obligation for finding $findingId is duplicated"};$obligationMap[$findingId]=@{severity=$severity;subject_id=$subjectId;status=$status;safe_action=$safeAction}}
    foreach($gateId in $requiredGateIds){if(-not$packetGates.ContainsKey($gateId)){Add-ValidationError "$label references missing authority gate $gateId"}}
    $subject=if($manifest.subjects.ContainsKey($subjectId)){$manifest.subjects[$subjectId]}else{@{}}
    if(-not(Test-Ordinal $owner $subject.accountable_owner_principal_id)){Add-ValidationError "$label.owner principal differs from source manifest"}
    if((Test-Ordinal $status "open-blocker")-or(Test-Ordinal $status "contested-blocker")){if(-not(Test-Ordinal $safeAction $subject.required_safe_action)){Add-ValidationError "$label.safe action conflicts with source manifest"};if((Test-Ordinal $status "contested-blocker")-and$refs.Count-eq0){Add-ValidationError "$label.contested blocker requires manifest evidence"}}
    elseif(Test-Ordinal $status "verified-closed"){if($null-ne$safeAction){Add-ValidationError "$label.verified closure must set safe_action_if_open to null"};if(-not(Test-InSet $verifiedBy $manifest.authorized_verifiers)){Add-ValidationError "$label.verified_by is not authorized by manifest"};if((Test-InSet $severity @("P0","P1"))-and(Test-Ordinal $verifiedBy $owner)){Add-ValidationError "$label.P0/P1 closure is not independent"};if(-not(Test-EvidenceCoverage $refs $requiredKeys $subjectId $manifest $verifiedBy)){Add-ValidationError "$label.closure does not cover every required evidence key"}}
}
if(-not(Test-SameKeys $obligationMap $manifest.findings)){Add-ValidationError "packet obligation IDs do not exactly match source findings"}

$subjectResults=New-OrdinalDictionary;$packetSubjectIds=New-OrdinalSet
for($index=0;$index-lt$controlPackets.Count;$index++){
    $controlPacket=$controlPackets[$index];$label="operating_controls[$index]";Test-ExactObjectKeys $controlPacket @("subject_id","subject_kind","risk_level","current_state","recommended_action","money_affected","accountable_owner_principal_id","controls") $label;$subjectId=Require-String $controlPacket "subject_id" $label;$subjectKind=Require-String $controlPacket "subject_kind" $label;$riskLevel=Require-String $controlPacket "risk_level" $label;$currentState=Require-String $controlPacket "current_state" $label;$recommendedAction=Require-String $controlPacket "recommended_action" $label;$moneyAffected=Require-Bool $controlPacket "money_affected" $label;$ownerPrincipal=Require-String $controlPacket "accountable_owner_principal_id" $label;$controls=Get-Value $controlPacket "controls"
    Require-Enum $subjectKind $subjectKinds "$label.subject_kind";Require-Enum $riskLevel $riskLevels "$label.risk_level";Require-Enum $recommendedAction ($safeActions+$advanceActions) "$label.recommended_action"
    $source=if($manifest.subjects.ContainsKey($subjectId)){$manifest.subjects[$subjectId]}else{$null};if($null-eq$source-and$subjectId){Add-ValidationError "$label.subject_id is not required by source manifest";$source=@{allowed_not_applicable=@();required_safe_action="";accountable_owner_principal_id=""}}elseif($null-ne$source){if(-not(Test-Ordinal $subjectKind $source.subject_kind)){Add-ValidationError "$label.subject_kind differs from source manifest"};if(-not(Test-Ordinal $riskLevel $source.risk_level)){Add-ValidationError "$label.risk_level differs from source manifest"};if(-not(Test-Ordinal $currentState $source.current_state)){Add-ValidationError "$label.current_state differs from source manifest"};if($moneyAffected-ne$source.money_affected){Add-ValidationError "$label.money_affected differs from source manifest"};if(-not(Test-Ordinal $ownerPrincipal $source.accountable_owner_principal_id)){Add-ValidationError "$label.accountable_owner_principal_id differs from source manifest"}}
    if(-not$packetSubjectIds.Add($subjectId)){Add-ValidationError "operating control subject $subjectId is duplicated"}
    if($null-eq$controls-or$controls-is[string]-or$controls-is[ValueType]-or$controls-is[System.Array]){Add-ValidationError "$label.controls must be an object";$controls=[pscustomobject]@{}};Test-ExactControlKeys $controls "$label.controls"
    $controlStates=New-OrdinalDictionary;$blockingFields=[System.Collections.Generic.List[string]]::new()
    foreach($field in $controlFields){$fieldLabel="$label.controls.$field";$control=Get-Value $controls $field;if($null-eq$control-or$control-is[string]-or$control-is[ValueType]-or$control-is[System.Array]){Add-ValidationError "$fieldLabel must be an object";continue};Test-ExactObjectKeys $control @("status","evidence_refs","rationale") $fieldLabel;$status=Require-String $control "status" $fieldLabel;$refs=@(Get-EvidenceRefs (Get-Value $control "evidence_refs") "$fieldLabel.evidence_refs" $manifest);$rationale=Require-String $control "rationale" $fieldLabel;Require-Enum $status $controlStatuses "$fieldLabel.status";if((Test-Ordinal $status "verified")-and-not(Test-EvidenceCoverage $refs @("control:$field") $subjectId $manifest)){Add-ValidationError "$fieldLabel.verified control lacks matching manifest evidence"};if((Test-Ordinal $status "verified")-and-not(Test-Ordinal $rationale (Get-EvidenceRationale $refs))){Add-ValidationError "$fieldLabel.verified control rationale is not canonical"};if((Test-Ordinal $status "not-applicable")-and-not(Test-InSet $field $source.allowed_not_applicable)){Add-ValidationError "$fieldLabel.not-applicable is not allowed by source manifest"};if((Test-Ordinal $status "not-applicable")-and(Test-InSet $riskLevel @("high","critical"))){$mandatory=(Test-InSet $field $mandatoryHighRiskControls)-or((Test-Ordinal $field "support_surface")-and(Test-InSet $subjectKind @("product-asset","external-paused-product")))-or((Test-Ordinal $field "reconciliation")-and$moneyAffected);if($mandatory){Add-ValidationError "$fieldLabel.not-applicable violates the high-risk applicability matrix"}};if(Test-InSet $status @("declared-unverified","proposed","missing-blocker")){$blockingFields.Add($field)};$controlStates[$field]=$status}
    $openHigh=[System.Collections.Generic.List[string]]::new();foreach($findingId in $obligationMap.Keys){$obligation=$obligationMap[$findingId];if((Test-Ordinal $obligation.subject_id $subjectId)-and(Test-InSet $obligation.severity @("P0","P1"))-and-not(Test-Ordinal $obligation.status "verified-closed")){$openHigh.Add($findingId)}}
    $unsatisfied=[System.Collections.Generic.List[string]]::new();foreach($gateId in $packetGates.Keys){$gate=$packetGates[$gateId];if((Test-Ordinal $gate.subject_id $subjectId)-and(Test-Ordinal $gate.status "required")){$unsatisfied.Add($gateId)}}
    $openArray=@($openHigh|Sort-Object -CaseSensitive);$blockArray=@($blockingFields|Sort-Object -CaseSensitive);$gateArray=@($unsatisfied|Sort-Object -CaseSensitive);$blockers=$openArray.Count-gt0-or$blockArray.Count-gt0-or$gateArray.Count-gt0;$advancementAllowed=(-not$blockers)-and(Test-InSet $recommendedAction $advanceActions)
    if((Test-InSet $recommendedAction $safeActions)-and-not(Test-Ordinal $recommendedAction $source.required_safe_action)){Add-ValidationError "$label.safe action conflicts with source manifest"};if($blockers-and-not(Test-Ordinal $recommendedAction $source.required_safe_action)){Add-ValidationError "$label.blockers require the manifest safe action"};if((Test-InSet $recommendedAction $advanceActions)-and$blockers){Add-ValidationError "$label attempts advancement while blockers remain"};$subjectGates=@($packetGates.Values|Where-Object{Test-Ordinal $_.subject_id $subjectId});if((Test-InSet $recommendedAction $advanceActions)-and$subjectGates.Count-gt0-and@($subjectGates|Where-Object{Test-Ordinal $_.action $recommendedAction}).Count-eq0){Add-ValidationError "$label.advancement action lacks an exact manifest gate"}
    if((Test-InSet $recommendedAction $advanceActions)-and(Test-InSet $riskLevel @("high","critical"))){foreach($state in $controlStates.Values){if(-not(Test-InSet $state @("verified","not-applicable"))){Add-ValidationError "$label.high-risk advancement lacks verified controls";break}}}
    if($blockers){$warnings.Add("$subjectId remains non-advancing until manifest-bound blockers close")};$subjectResults[$subjectId]=@{recommended_action=$recommendedAction;advancement_allowed=$advancementAllowed;open_high=$openArray;blocking_controls=$blockArray;unsatisfied_gates=$gateArray}
}
$manifestSubjectSet=New-OrdinalSet;foreach($key in $manifest.subjects.Keys){[void]$manifestSubjectSet.Add($key)};if($packetSubjectIds.Count-ne$manifestSubjectSet.Count){Add-ValidationError "packet operating-control subjects do not exactly match manifest"}else{foreach($key in $packetSubjectIds){if(-not$manifestSubjectSet.Contains($key)){Add-ValidationError "packet operating-control subjects do not exactly match manifest";break}}}

$valid=$errors.Count-eq0;$delivery=$null;$deliverySha=$null;if($valid){$delivery=Get-CanonicalDelivery $decisionId $manifest.manifest_id $manifest.sha256 $subjectResults;$deliverySha=Get-StringShaLower $delivery}
$advancement=[ordered]@{};foreach($key in @($subjectResults.Keys|Sort-Object -CaseSensitive)){$advancement[$key]=[bool]($valid-and$subjectResults[$key].advancement_allowed)}
$openAll=[System.Collections.Generic.List[string]]::new();$controlAll=[System.Collections.Generic.List[string]]::new();$gateAll=[System.Collections.Generic.List[string]]::new()
foreach($subjectId in $subjectResults.Keys){foreach($id in @($subjectResults[$subjectId].open_high)){$openAll.Add($id)};foreach($field in @($subjectResults[$subjectId].blocking_controls)){$controlAll.Add("$($subjectId):$field")};foreach($id in @($subjectResults[$subjectId].unsatisfied_gates)){$gateAll.Add($id)}}
$result=[ordered]@{valid=$valid;schema_version=$packetVersion;manifest_version=$manifestVersion;decision_id=$decisionId;manifest_id=$manifest.manifest_id;manifest_sha256=$manifest.sha256;expected_manifest_sha256=$ExpectedManifestSha;advancement_allowed_by_subject=$advancement;open_high_severity_obligations=@($openAll|Sort-Object -CaseSensitive -Unique);blocking_control_fields=@($controlAll|Sort-Object -CaseSensitive -Unique);unsatisfied_authority_gates=@($gateAll|Sort-Object -CaseSensitive -Unique);canonical_delivery_markdown=$delivery;canonical_delivery_sha256=$deliverySha;errors=@($errors);warnings=@($warnings|Sort-Object -CaseSensitive -Unique)}
Write-ResultAndExit $result $(if($valid){0}else{2})
