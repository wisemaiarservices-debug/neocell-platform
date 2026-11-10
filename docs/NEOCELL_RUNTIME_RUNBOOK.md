# NeoCell Runtime Runbook

## Purpose

The NeoCell runtime is a decision-support API contract for infrastructure inventory and future edge telemetry integration. The current V1 runtime demonstrates input validation and provenance handling; it is not yet connected to gateways, sensor nodes, battery-management systems or commissioned site assets.

## Run locally

```powershell
cd runtime
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
uvicorn app:app --reload --port 8300
```

## Verify

- API process health: `http://localhost:8300/health`
- Demonstration contract: `http://localhost:8300/api/v1/dashboard/summary`
- OpenAPI docs: `http://localhost:8300/docs`

The health endpoint confirms only that the API process responds. It does not establish device connectivity or telemetry validity.

## Smoke test

From repository root:

```powershell
.\scripts\smoke-api.ps1
```

## Test

```powershell
cd runtime
pytest
```

## API endpoints

- `GET /health` — API process health only.
- `GET /api/v1/dashboard/summary` — synthetic default inputs with field-level provenance.
- `POST /api/v1/readiness/analyze` — returns `not_assessed` until validated telemetry and calibrated methods exist.
- `POST /api/v1/plans/run` — returns `not_estimable_from_available_inputs`; no operational actions are generated.
- `POST /api/v1/recommendations/run` — human-review checklist only; confidence and expected impact remain null.

## Data provenance contract

- Defaults are labelled `synthetic_defaults`.
- Partial caller inputs are labelled `mixed_synthetic_and_caller_supplied`.
- Fully supplied values are labelled `caller_supplied_unverified`.
- Caller-supplied values are not trusted as measurements until device identity, source, timestamp, units, calibration and integrity are validated.
- Unknown fields and out-of-range values are rejected.
- CORS can be configured with the comma-separated `NEOCELL_ALLOWED_ORIGINS` environment variable. Local development origins are the defaults.

## Requirements before field deployment

1. Define device identity and enrollment, including key rotation and revocation.
2. Add authenticated ingestion with replay protection and per-device authorization.
3. Define canonical observation schemas with event time, ingestion time, units, quality flags and provenance.
4. Validate sensor calibration, clock drift, missingness, duplicates and outliers.
5. Persist observations and asset records with retention and audit controls.
6. Establish site-specific baselines and validate any readiness model against labelled field data.
7. Require qualified human approval for maintenance and infrastructure decisions.

## Current limitations

No live telemetry, site coordinates, commissioned inventory, trained ML, calibrated readiness score, maintenance optimizer or autonomous control is included. No pilot location is assumed. The UI and API must continue to distinguish demonstration inputs from verified field observations.
