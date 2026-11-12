from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field


class CellState(BaseModel):
    """Input contract; omitted measurements stay unknown and are never device telemetry."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    site_id: str | None = None
    gateway_online_pct: float | None = Field(default=None, ge=0, le=100)
    sensor_online_pct: float | None = Field(default=None, ge=0, le=100)
    battery_node_soc_pct: float | None = Field(default=None, ge=0, le=100)
    data_latency_ms: float | None = Field(default=None, ge=0, le=600000)
    temperature_c: float | None = Field(default=None, ge=-80, le=85)
    dust_risk_pct: float | None = Field(default=None, ge=0, le=100)
    pump_node_health_pct: float | None = Field(default=None, ge=0, le=100)
    water_node_health_pct: float | None = Field(default=None, ge=0, le=100)


class CellRecommendation(BaseModel):
    id: str
    title: str
    priority: str
    confidence: float | None = None
    explanation: str
    expected_impact: dict[str, Any]
    status: str = "review_required"
    requires_operator_review: bool = True


ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "NEOCELL_ALLOWED_ORIGINS",
        "http://localhost:8400,http://localhost:8504,http://127.0.0.1:8504",
    ).split(",")
    if origin.strip()
]

app = FastAPI(title="NeoCell API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def input_provenance(state: CellState) -> dict[str, Any]:
    measurement_fields = set(type(state).model_fields) - {"site_id"}
    provided = sorted(state.model_fields_set)
    provided_measurements = sorted(measurement_fields.intersection(state.model_fields_set))
    missing_measurements = sorted(measurement_fields - set(provided_measurements))
    mode = "caller_supplied_unverified" if provided_measurements else "insufficient_inputs"
    return {
        "data_mode": mode,
        "provided_fields": provided,
        "provided_measurement_fields": provided_measurements,
        "defaulted_fields": [],
        "missing_fields": missing_measurements,
        "synthetic_defaults_present": False,
        "caller_supplied_values_verified": False,
        "note": (
            "No measurement defaults are populated. Caller-supplied values remain "
            "unverified until source/device identity, timestamps, units and calibration "
            "are checked."
        ),
    }

def methodology() -> dict[str, Any]:
    return {
        "type": "input_contract_and_provenance_only",
        "version": "neocell-readiness-screening-v0.2",
        "calibrated_readiness_model": False,
        "trained_machine_learning": False,
        "live_device_telemetry": False,
        "automated_control": False,
        "limitations": [
            "No authenticated gateway or sensor feed is connected.",
            "No commissioned asset inventory or site-specific baseline is available.",
            "No validated reliability, heat, dust or battery health model is available.",
            "No maintenance action, expected benefit or downtime reduction is estimated.",
            "All operational decisions require qualified human review.",
        ],
    }


def metadata(state: CellState) -> dict[str, Any]:
    return {
        "input_provenance": input_provenance(state),
        "methodology": methodology(),
        "requires_operator_review": True,
    }


def summary(state: CellState) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "scenario": "NeoCell input contract · no assumed site or device measurements",
        "readiness_score": None,
        "readiness_status": "not_assessed",
        "kpis": [
            {"label": "Gateway online input", "value": state.gateway_online_pct, "unit": "%", "interpretation": "unverified input"},
            {"label": "Sensor online input", "value": state.sensor_online_pct, "unit": "%", "interpretation": "unverified input"},
            {"label": "Edge battery input", "value": state.battery_node_soc_pct, "unit": "%", "interpretation": "unverified input"},
            {"label": "Data latency input", "value": state.data_latency_ms, "unit": "ms", "interpretation": "unverified input"},
            {"label": "Temperature input", "value": state.temperature_c, "unit": "°C", "interpretation": "unverified input"},
            {"label": "Dust risk input", "value": state.dust_risk_pct, "unit": "%", "interpretation": "unverified input"},
        ],
        "generated_at": now_iso(),
        **metadata(state),
    }


def analyze(state: CellState) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "status": "not_assessed",
        "readiness_score": None,
        "heat_exposure": None,
        "dust_exposure": None,
        "data_quality": "unverified",
        "reason": "Validated telemetry, asset metadata, timestamps, calibration and site-specific thresholds are required.",
        "generated_at": now_iso(),
        **metadata(state),
    }


def plan(state: CellState) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "status": "not_estimable_from_available_inputs",
        "plan": None,
        "actions": [],
        "expected_data_reliability_gain_pct": None,
        "expected_downtime_risk_reduction_pct": None,
        "expected_response_time_gain_pct": None,
        "reason": "No verified device inventory, maintenance history, operating limits or validated intervention evidence is connected.",
        "generated_at": now_iso(),
        **metadata(state),
    }


def recommend(state: CellState) -> CellRecommendation:
    return CellRecommendation(
        id="neocell-review-verify-telemetry-001",
        title="Verify gateway, sensor and asset records before readiness assessment",
        priority="review_required",
        confidence=None,
        explanation=(
            "NeoCell has no authenticated field telemetry or validated readiness model. "
            "The next safe step is to verify device identity, timestamps, units, calibration "
            "and commissioned asset records."
        ),
        expected_impact={
            "data_reliability_gain_pct": None,
            "downtime_risk_reduction_pct": None,
            "response_time_gain_pct": None,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "neocell-api",
        "mode": "decision_support_only",
        "time": now_iso(),
    }


@app.get("/api/v1/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    state = CellState()
    return {
        **summary(state),
        "analysis": analyze(state),
        "plan": plan(state),
        "recommendations": [recommend(state).model_dump()],
    }


@app.post("/api/v1/readiness/analyze")
def run_analysis(state: CellState) -> dict[str, Any]:
    return analyze(state)


@app.post("/api/v1/plans/run")
def run_plan(state: CellState) -> dict[str, Any]:
    return plan(state)


@app.post("/api/v1/recommendations/run")
def run_recommendations(state: CellState) -> dict[str, Any]:
    return {
        "status": "review_required",
        "recommendations": [recommend(state).model_dump()],
        "generated_at": now_iso(),
        **metadata(state),
    }
