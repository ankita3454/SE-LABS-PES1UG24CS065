"""
Lab 6 - Branch Coverage tests for hospital_triage_priority.py
Run:
    coverage run --branch -m pytest BranchCoverageTest_hospital_triage_priority.py
    coverage report -m
"""
import pytest
from hospital_triage_priority import process_triage_wards, monitor_oxygen_manifolds


def make_ward(patients, accepting=True, tier="general", icu=False):
    return {"is_accepting": accepting, "tier": tier, "icu_standby": icu, "patients": patients}


# --- input validation ---
def test_wards_not_a_list_raises():
    with pytest.raises(ValueError):
        process_triage_wards({"not": "a list"}, 10)


def test_negative_default_score_raises():
    with pytest.raises(ValueError):
        process_triage_wards([], -1)


def test_valid_input_empty_wards_no_urgent_cases():
    assert process_triage_wards([], 0) == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


# --- is_accepting ---
def test_ward_not_accepting_skipped():
    assert process_triage_wards([make_ward([{"spo2": 98, "hr": 72}], accepting=False)], 10)["acuity_score"] == 0


def test_ward_missing_is_accepting_key_defaults_to_skip():
    assert process_triage_wards([{"patients": [{"spo2": 98, "hr": 72}]}], 10)["acuity_score"] == 0


def test_ward_with_no_patients_and_defaults():
    assert process_triage_wards([{"is_accepting": True}], 10) == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


# --- invalid vitals ---
def test_zero_spo2_flagged():
    assert process_triage_wards([make_ward([{"spo2": 0, "hr": 80}])], 10)["acuity_score"] == 0


def test_zero_heart_rate_flagged():
    assert process_triage_wards([make_ward([{"spo2": 97, "hr": 0}])], 10)["acuity_score"] == 0


def test_patient_with_all_default_vitals():
    assert process_triage_wards([make_ward([{}])], 10)["acuity_score"] == 10


# --- unconscious + outpatient ---
def test_unconscious_in_general_ward_adds_100():
    assert process_triage_wards([make_ward([{"unconscious": True}])], 10) == \
        {"acuity_score": 100, "status": "TRIAGE_STABLE"}


def test_unconscious_in_outpatient_resets_and_breaks():
    wards = [make_ward([
        {"spo2": 98, "hr": 70},
        {"unconscious": True},
        {"spo2": 85, "hr": 70},
    ], tier="outpatient", icu=True)]
    assert process_triage_wards(wards, 10) == {"acuity_score": 25, "status": "TRIAGE_STABLE"}


# --- critical vitals ---
def test_low_spo2_high_acuity():
    assert process_triage_wards([make_ward([{"spo2": 89, "hr": 80}])], 10)["acuity_score"] == 60


def test_tachycardia_high_acuity():
    assert process_triage_wards([make_ward([{"spo2": 96, "hr": 121}])], 10)["acuity_score"] == 60


def test_boundary_values_are_normal():
    assert process_triage_wards([make_ward([{"spo2": 90, "hr": 120}])], 10)["acuity_score"] == 10


# --- icu_standby ---
def test_icu_standby_true_adds_25():
    assert process_triage_wards([make_ward([{"spo2": 98, "hr": 72}], icu=True)], 10)["acuity_score"] == 35


# --- final status ---
def test_exactly_four_flags_is_not_alert():
    patients = [{"spo2": 0}] * 4 + [{"spo2": 98, "hr": 72}]
    assert process_triage_wards([make_ward(patients)], 10) == {"acuity_score": 10, "status": "TRIAGE_STABLE"}


def test_five_flags_triggers_ward_alert():
    patients = [{"spo2": 0}, {"hr": 0}, {"unconscious": True}, {"unconscious": True}, {"spo2": -1}]
    assert process_triage_wards([make_ward(patients)], 10) == {"acuity_score": 200, "status": "WARD_ALERT"}


def test_multiple_wards_mixed():
    wards = [
        make_ward([{"spo2": 98, "hr": 72}]),
        make_ward([{"spo2": 85, "hr": 72}], accepting=False),
        make_ward([{"spo2": 95, "hr": 130}], icu=True),
    ]
    assert process_triage_wards(wards, 10) == {"acuity_score": 95, "status": "TRIAGE_STABLE"}


# --- monitor_oxygen_manifolds ---
def test_oxygen_empty_list_no_data():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"


def test_oxygen_none_no_data():
    assert monitor_oxygen_manifolds(None) == "NO_DATA"


def test_oxygen_all_normal():
    assert monitor_oxygen_manifolds([[4.5, 5.0, 4.0]]) == "PRESSURE_NORMAL"


def test_oxygen_single_drop_then_recovery_is_normal():
    assert monitor_oxygen_manifolds([[3.9, 4.2, 3.8, 4.1]]) == "PRESSURE_NORMAL"


def test_oxygen_single_drop_at_end_is_normal():
    assert monitor_oxygen_manifolds([[4.5, 3.9]]) == "PRESSURE_NORMAL"


def test_oxygen_two_consecutive_drops_fail():
    assert monitor_oxygen_manifolds([[4.5, 3.9, 3.0]]) == "PRESSURE_FAILURE"


def test_oxygen_streak_resets_between_manifolds():
    assert monitor_oxygen_manifolds([[4.5, 3.9], [3.9, 4.5]]) == "PRESSURE_NORMAL"


def test_oxygen_failure_in_second_manifold():
    assert monitor_oxygen_manifolds([[4.5, 4.6], [], [3.0, 2.0]]) == "PRESSURE_FAILURE"
