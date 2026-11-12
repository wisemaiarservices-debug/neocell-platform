$ErrorActionPreference = "Stop"
$BaseUrl = $env:NEOCELL_API_URL
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  $BaseUrl = "http://localhost:8300"
}

Write-Host "Testing NeoCell API at $BaseUrl" -ForegroundColor Cyan

try {
  $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10
  if ($health.status -ne "ok") { throw "Expected status ok" }
  if ($health.service -ne "neocell-api") { throw "Expected service neocell-api" }
  if ($health.mode -ne "decision_support_only") { throw "Expected decision_support_only mode" }

  $summary = Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboard/summary" -Method GET -TimeoutSec 10
  if ($summary.scenario -ne "NeoCell input contract · no assumed site or device measurements") { throw "Unexpected scenario" }
  if ($summary.readiness_status -ne "not_assessed") { throw "Readiness must remain not_assessed" }
  if ($null -ne $summary.readiness_score) { throw "Readiness score must not be fabricated" }
  if ($summary.input_provenance.data_mode -ne "insufficient_inputs") { throw "Expected insufficient_inputs provenance" }
  if ($summary.input_provenance.synthetic_defaults_present -ne $false) { throw "Synthetic defaults must be absent" }
  if ($summary.input_provenance.defaulted_fields.Count -ne 0) { throw "No fields may be defaulted" }
  if ($null -ne $summary.site_id) { throw "Site ID must remain unknown" }
  foreach ($kpi in $summary.kpis) { if ($null -ne $kpi.value) { throw "Dashboard KPI values must remain unknown" } }
  if ($summary.analysis.status -ne "not_assessed") { throw "Analysis must remain not_assessed" }
  if ($summary.plan.status -ne "not_estimable_from_available_inputs") { throw "Plan must remain not_estimable" }
  if ($summary.recommendations.Count -lt 1) { throw "Expected a review checklist" }
  if ($null -ne $summary.recommendations[0].confidence) { throw "Recommendation confidence must remain null" }

  Write-Host "NeoCell API smoke test passed." -ForegroundColor Green
  exit 0
} catch {
  Write-Host "NeoCell API smoke test failed." -ForegroundColor Red
  Write-Host $_.Exception.Message
  exit 1
}
