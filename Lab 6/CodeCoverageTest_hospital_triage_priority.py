"""
Lab 6 - Code (Line) Coverage tests for hospital_triage_priority.py
Run:
    coverage run -m pytest CodeCoverageTest_hospital_triage_priority.py
    coverage report -m
"""
import pytest
from hospital_triage_priority import process_triage_wards, monitor_oxygen_manifolds


def make_ward(patients, accepting=True, tier="general", icu=False):
    return {"is_accepting": accepting, "tier": tier, "icu_standby": icu, "patients": patients}


def test_single_normal_patient():
    result = process_triage_wards([make_ward([{"spo2": 98, "hr": 72, "unconscious": False}])], 10)
    assert result == {"acuity_score": 10, "status": "TRIAGE_STABLE"}


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        process_triage_wards("not a list", 10)


def test_non_accepting_ward_is_skipped():
    result = process_triage_wards([make_ward([{"spo2": 98, "hr": 72}], accepting=False)], 10)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_invalid_vitals_are_flagged_and_skipped():
    result = process_triage_wards([make_ward([{"spo2": 0, "hr": 80}])], 10)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_unconscious_patient_general_ward():
    result = process_triage_wards([make_ward([{"spo2": 95, "hr": 80, "unconscious": True}])], 10)
    assert result == {"acuity_score": 100, "status": "TRIAGE_STABLE"}


def test_unconscious_patient_outpatient_resets_and_breaks():
    wards = [make_ward([
        {"spo2": 98, "hr": 70},
        {"spo2": 95, "hr": 80, "unconscious": True},
        {"spo2": 98, "hr": 70},
    ], tier="outpatient")]
    result = process_triage_wards(wards, 10)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_low_spo2_is_high_acuity():
    result = process_triage_wards([make_ward([{"spo2": 85, "hr": 80}])], 10)
    assert result == {"acuity_score": 60, "status": "TRIAGE_STABLE"}


def test_icu_standby_adds_bonus():
    result = process_triage_wards([make_ward([{"spo2": 98, "hr": 72}], icu=True)], 10)
    assert result == {"acuity_score": 35, "status": "TRIAGE_STABLE"}


def test_more_than_four_flags_raises_ward_alert():
    patients = [{"spo2": 0, "hr": 80} for _ in range(5)]
    result = process_triage_wards([make_ward(patients)], 10)
    assert result == {"acuity_score": 0, "status": "WARD_ALERT"}


def test_oxygen_no_data():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"


def test_oxygen_two_consecutive_drops_fail():
    assert monitor_oxygen_manifolds([[5.0, 3.9, 3.5]]) == "PRESSURE_FAILURE"


def test_oxygen_normal_with_streak_reset():
    assert monitor_oxygen_manifolds([[3.9, 4.5, 3.8, 4.2]]) == "PRESSURE_NORMAL"
