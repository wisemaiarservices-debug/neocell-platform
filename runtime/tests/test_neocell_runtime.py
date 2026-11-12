import pytest

from runtime.app import CellState, analyze, input_provenance, plan, recommend, summary


def test_empty_inputs_do_not_create_synthetic_site_or_device_measurements():
    state = CellState()
    provenance = input_provenance(state)
    assert state.site_id is None
    assert state.gateway_online_pct is None
    assert provenance["data_mode"] == "insufficient_inputs"
    assert provenance["defaulted_fields"] == []
    assert provenance["synthetic_defaults_present"] is False
    assert "gateway_online_pct" in provenance["missing_fields"]


def test_site_identity_alone_is_not_reported_as_device_telemetry():
    provenance = input_provenance(CellState(site_id="registered-site-001"))
    assert provenance["data_mode"] == "insufficient_inputs"
    assert provenance["provided_fields"] == ["site_id"]
    assert provenance["provided_measurement_fields"] == []
    assert "gateway_online_pct" in provenance["missing_fields"]


def test_partial_caller_inputs_remain_unverified_without_filling_other_fields():
    state = CellState(gateway_online_pct=80)
    provenance = input_provenance(state)
    assert provenance["data_mode"] == "caller_supplied_unverified"
    assert "gateway_online_pct" in provenance["provided_fields"]
    assert "sensor_online_pct" in provenance["missing_fields"]
    assert state.sensor_online_pct is None


def test_summary_does_not_publish_unvalidated_readiness_score():
    result = summary(CellState())
    assert result["readiness_score"] is None
    assert result["readiness_status"] == "not_assessed"
    assert all(item["interpretation"] == "unverified input" for item in result["kpis"])
    assert result["methodology"]["calibrated_readiness_model"] is False


def test_analysis_withholds_exposure_and_data_quality_assessment():
    result = analyze(CellState(temperature_c=39, dust_risk_pct=80))
    assert result["status"] == "not_assessed"
    assert result["heat_exposure"] is None
    assert result["dust_exposure"] is None
    assert result["data_quality"] == "unverified"


def test_plan_has_no_unvalidated_actions_or_impact_claims():
    result = plan(CellState())
    assert result["status"] == "not_estimable_from_available_inputs"
    assert result["actions"] == []
    assert result["expected_data_reliability_gain_pct"] is None
    assert result["expected_downtime_risk_reduction_pct"] is None


def test_recommendation_is_review_only_without_confidence_or_impact():
    rec = recommend(CellState()).model_dump()
    assert rec["status"] == "review_required"
    assert rec["confidence"] is None
    assert rec["requires_operator_review"] is True
    assert rec["expected_impact"]["data_reliability_gain_pct"] is None


def test_non_finite_measurements_are_rejected():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            CellState(temperature_c=value)


def test_input_bounds_and_extra_fields_are_rejected():
    with pytest.raises(ValueError):
        CellState(gateway_online_pct=140)
    with pytest.raises(ValueError):
        CellState(data_latency_ms=-1)
    with pytest.raises(ValueError):
        CellState(unexpected_input=1)
