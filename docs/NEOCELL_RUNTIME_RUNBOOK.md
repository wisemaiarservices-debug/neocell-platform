# NeoCell Runtime Runbook

## Purpose

This runtime provides the first runnable NOVA Infrastructure / NeoCell API for the SolarHub demo.

It supports the agrivoltaic demo by showing site readiness, gateway status, sensor status, edge battery reserve, data latency, and operator recommendations.

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

```text
http://localhost:8300/health
http://localhost:8300/api/v1/dashboard/summary
```

## Smoke test

From repo root:

```powershell
.\scripts\smoke-api.ps1
```

## Test

```powershell
cd runtime
pytest
```

## API endpoints

- `GET /health`
- `GET /api/v1/dashboard/summary`
- `POST /api/v1/readiness/analyze`
- `POST /api/v1/plans/run`
- `POST /api/v1/recommendations/run`

## Demo Story

A heatwave is forecast. NeoCell checks gateways, sensor nodes, edge battery reserve, data latency, pump node health, and water node health before NeoAgro and NeoGrid optimize the site.
