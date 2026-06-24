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

  $summary = Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboard/summary" -Method GET -TimeoutSec 10
  if ($summary.scenario -ne "SolarHub site readiness and edge telemetry") { throw "Unexpected scenario" }
  if ($summary.kpis.Count -lt 6) { throw "Expected at least 6 KPIs" }
  if ($summary.recommendations.Count -lt 1) { throw "Expected at least 1 recommendation" }

  Write-Host "NeoCell API smoke test passed." -ForegroundColor Green
  exit 0
} catch {
  Write-Host "NeoCell API smoke test failed." -ForegroundColor Red
  Write-Host $_.Exception.Message
  exit 1
}
