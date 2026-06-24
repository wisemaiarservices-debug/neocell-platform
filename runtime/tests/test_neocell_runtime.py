from runtime.app import CellState, analyze, plan, readiness_score, recommend


def test_readiness_score_range():
    score = readiness_score(CellState())
    assert 0 <= score <= 100
    assert score >= 80


def test_analysis_heat_exposure():
    result = analyze(CellState(temperature_c=39))
    assert result["heat_exposure"] == "high"
    assert result["data_quality"] == "good"


def test_plan_contains_actions():
    result = plan(CellState())
    assert result["expected_data_reliability_gain_pct"] > 0
    assert len(result["actions"]) >= 3


def test_recommendation_operator_review():
    rec = recommend(CellState())
    assert "readiness" in rec.title.lower()
    assert rec.status == "operator_review"
    assert rec.confidence > 0.5
