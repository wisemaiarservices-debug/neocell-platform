from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class CellState(BaseModel):
    site_id: str = "site-solarhub-agro-001"
    gateway_online_pct: float = 94
    sensor_online_pct: float = 89
    battery_node_soc_pct: float = 72
    data_latency_ms: float = 420
    temperature_c: float = 39
    dust_risk_pct: float = 36
    pump_node_health_pct: float = 88
    water_node_health_pct: float = 91


class CellRecommendation(BaseModel):
    id: str
    title: str
    priority: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    expected_impact: dict[str, Any]
    status: str = "operator_review"


app = FastAPI(title="NeoCell API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def readiness_score(state: CellState) -> int:
    score = (
        state.gateway_online_pct * 0.25
        + state.sensor_online_pct * 0.25
        + state.battery_node_soc_pct * 0.15
        + state.pump_node_health_pct * 0.15
        + state.water_node_health_pct * 0.20
    )
    latency_penalty = 4 if state.data_latency_ms > 500 else 0
    heat_penalty = 3 if state.temperature_c >= 38 else 0
    return max(0, min(100, round(score - latency_penalty - heat_penalty)))


def summary(state: CellState = CellState()) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "scenario": "SolarHub site readiness and edge telemetry",
        "readiness_score": readiness_score(state),
        "kpis": [
            {"label": "Gateway Online", "value": state.gateway_online_pct, "unit": "%", "trend": "stable"},
            {"label": "Sensor Online", "value": state.sensor_online_pct, "unit": "%", "trend": "up"},
            {"label": "Node Battery", "value": state.battery_node_soc_pct, "unit": "%", "trend": "stable"},
            {"label": "Data Latency", "value": state.data_latency_ms, "unit": "ms", "trend": "down"},
            {"label": "Pump Node", "value": state.pump_node_health_pct, "unit": "%", "trend": "stable"},
            {"label": "Water Node", "value": state.water_node_health_pct, "unit": "%", "trend": "up"},
        ],
        "generated_at": now_iso(),
    }


def analyze(state: CellState) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "readiness_score": readiness_score(state),
        "heat_exposure": "high" if state.temperature_c >= 38 else "medium",
        "dust_exposure": "medium_high" if state.dust_risk_pct >= 35 else "medium",
        "data_quality": "good" if state.sensor_online_pct >= 85 and state.data_latency_ms <= 600 else "needs_attention",
        "edge_power_status": "good" if state.battery_node_soc_pct >= 60 else "watch",
        "generated_at": now_iso(),
    }


def plan(state: CellState) -> dict[str, Any]:
    return {
        "site_id": state.site_id,
        "plan": "pre_heatwave_readiness_check",
        "actions": [
            "Confirm gateway uplink before the heat window",
            "Prioritize soil and water node checks",
            "Keep edge battery reserve above 60 percent",
            "Schedule pump node inspection before irrigation shift",
        ],
        "expected_data_reliability_gain_pct": 8,
        "expected_downtime_risk_reduction_pct": 12,
        "expected_response_time_gain_pct": 10,
        "generated_at": now_iso(),
    }


def recommend(state: CellState) -> CellRecommendation:
    return CellRecommendation(
        id="neocell-rec-readiness-001",
        title="Run pre-heatwave site readiness check",
        priority="high" if state.temperature_c >= 38 else "medium",
        confidence=0.82,
        explanation=(
            "NeoCell detects high heat exposure with elevated field activity. A readiness check improves telemetry quality "
            "before irrigation and energy coordination decisions are made."
        ),
        expected_impact={
            "data_reliability_gain_pct": 8,
            "downtime_risk_reduction_pct": 12,
            "response_time_gain_pct": 10,
            "readiness_score_after_action": min(100, readiness_score(state) + 7),
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "neocell-api", "time": now_iso()}


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
    return {"status": "completed", "recommendations": [recommend(state).model_dump()], "generated_at": now_iso()}
