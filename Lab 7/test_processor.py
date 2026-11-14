"""
Lab 7 - Fuzz testing processor.py with Hypothesis.

Each function gets:
  1. A no-crash fuzz test over arbitrary text / None (the starter tests, completed).
  2. A targeted fuzz test that builds inputs out of the characters the parser
     actually cares about (digits, '.', ',', '/', '-', signs, 'nan', 'inf', ...),
     so Hypothesis reaches the deeper edge cases much faster than random Unicode.

Run:  pytest test_processor.py   (or: python -m pytest test_processor.py)
"""
from hypothesis import given, settings, strategies as st
from processor import parse_vitals_summary, compute_patient_bmi, assign_ward_bed

# Pieces that are meaningful to the parsers: numbers, separators and the
# special float spellings that float() happily accepts.
number_like = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.integers(min_value=-10**6, max_value=10**6).map(str),
    st.sampled_from(["", " ", "nan", "inf", "-inf", "0", "0.0", "-1", "1e309", "abc"]),
)


def joined(sep, min_size=0, max_size=5):
    return st.lists(number_like, min_size=min_size, max_size=max_size).map(sep.join)


# ---------------- parse_vitals_summary ----------------

@given(st.text() | st.none())
def test_parse_vitals_summary_no_crash(s):
    try:
        result = parse_vitals_summary(s)
    except Exception as e:
        assert False, f"parse_vitals_summary crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, str)


@settings(max_examples=300)
@given(joined(","))
def test_parse_vitals_summary_structured_no_crash(s):
    try:
        result = parse_vitals_summary(s)
    except Exception as e:
        assert False, f"parse_vitals_summary crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, str)
    # NaN / infinite vitals must never be reported as a real reading
    assert "nan" not in result.lower() and "inf" not in result.lower(), \
        f"non-finite vitals leaked into the summary: {result!r}"


# ---------------- compute_patient_bmi ----------------

@given(st.text() | st.none())
def test_compute_patient_bmi_safe(s):
    try:
        result = compute_patient_bmi(s)
    except Exception as e:
        assert False, f"compute_patient_bmi crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, (float, str))


@settings(max_examples=300)
@given(joined("/"))
def test_compute_patient_bmi_structured_safe(s):
    try:
        result = compute_patient_bmi(s)
    except Exception as e:
        assert False, f"compute_patient_bmi crashed on {s!r} with: {type(e).__name__}: {e}"
    if isinstance(result, float):
        # a BMI that is returned as a number must be a real, positive value
        assert result == result and result not in (float("inf"), float("-inf")), \
            f"non-finite BMI {result!r} for input {s!r}"
        assert result > 0, f"non-positive BMI {result!r} for input {s!r}"


# ---------------- assign_ward_bed ----------------

@given(st.text() | st.none())
def test_assign_ward_bed_safe(s):
    try:
        result = assign_ward_bed(s)
    except Exception as e:
        assert False, f"assign_ward_bed crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, str)


@settings(max_examples=300)
@given(
    st.sampled_from(["ER", "icu", "GEN", "Ped", "XYZ", "", " ICU "]),
    st.sampled_from(["-", "--", "", " - "]),
    st.one_of(st.integers(min_value=-1000, max_value=1000).map(str),
              st.sampled_from(["", "abc", "1.5", " 05 ", "0"])),
)
def test_assign_ward_bed_structured_safe(ward, sep, bed):
    code = f"{ward}{sep}{bed}"
    try:
        result = assign_ward_bed(code)
    except Exception as e:
        assert False, f"assign_ward_bed crashed on {code!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, str)
    if "Bed #" in result:
        bed_no = int(result.rsplit("#", 1)[1])
        assert bed_no >= 1, f"invalid bed number accepted: {code!r} -> {result!r}"
