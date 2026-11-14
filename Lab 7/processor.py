import math

# Bugs found by fuzzing (test_processor.py) and fixed here:
#   - None / non-string input  -> AttributeError on .split() / .strip()
#   - wrong number of fields   -> IndexError / "not enough / too many values to unpack"
#   - empty or non-numeric parts -> ValueError from float() / int()
#   - height of 0              -> ZeroDivisionError in BMI
#   - 'nan' / 'inf' accepted by float() -> NaN vitals reported as STABLE, inf/NaN BMI
#   - unknown ward code        -> KeyError
#   - bed numbers <= 0, '+5', ' 5', unicode digits accepted by int()
# Every function now validates its input and returns an "Invalid input: ..."
# message instead of raising.

WARD_NAMES = {
    "ER": "Emergency Room",
    "ICU": "Intensive Care Unit",
    "GEN": "General Ward",
    "PED": "Pediatrics",
}

MAX_INPUT_LEN = 100  # guards against huge inputs (DoS-style fuzz cases)


def _to_finite_float(text):
    """Convert text to a finite float, or raise ValueError."""
    value = float(text.strip())
    if not math.isfinite(value):
        raise ValueError("value must be a finite number")
    return value


def _check_text(value):
    if not isinstance(value, str):
        raise ValueError("expected a text string")
    if not value.strip():
        raise ValueError("input is empty")
    if len(value) > MAX_INPUT_LEN:
        raise ValueError("input is too long")


def parse_vitals_summary(vitals_csv):
    try:
        _check_text(vitals_csv)
        parts = vitals_csv.split(',')
        if len(parts) != 3:
            raise ValueError("expected exactly 3 values: HR,SpO2,Temp")
        hr, spo2, temp = (_to_finite_float(p) for p in parts)
        if not 0 < hr <= 300:
            raise ValueError("HR must be between 1 and 300 bpm")
        if not 0 < spo2 <= 100:
            raise ValueError("SpO2 must be between 1 and 100 %")
        if not 25.0 <= temp <= 45.0:
            raise ValueError("Temp must be between 25 and 45 degC")
    except ValueError as e:
        return f"Invalid input: {e}"

    critical = hr > 120 or spo2 < 90 or temp > 39.0
    return f"Vitals: HR={hr}, SpO2={spo2}% - {'CRITICAL' if critical else 'STABLE'}"


def compute_patient_bmi(bmi_string):
    try:
        _check_text(bmi_string)
        parts = bmi_string.split('/')
        if len(parts) != 2:
            raise ValueError("expected format weight/height, e.g. 70/1.75")
        weight = _to_finite_float(parts[0])
        height = _to_finite_float(parts[1])
        if not 0.5 <= weight <= 700:
            raise ValueError("weight must be between 0.5 and 700 kg")
        if not 0.3 <= height <= 3.0:
            raise ValueError("height must be between 0.3 and 3.0 m")
    except ValueError as e:
        return f"Invalid input: {e}"

    bmi = weight / (height ** 2)
    return round(bmi, 2)


def assign_ward_bed(allocation_code):
    try:
        _check_text(allocation_code)
        parts = allocation_code.strip().split('-')
        if len(parts) != 2:
            raise ValueError("expected format WARD-BED, e.g. ICU-05")
        ward = parts[0].strip().upper()
        bed_str = parts[1].strip()
        if ward not in WARD_NAMES:
            raise ValueError(f"unknown ward; use one of {', '.join(WARD_NAMES)}")
        # plain ASCII digits only: rejects '', '+5', '1_0', '1.5' and unicode digits
        if not (bed_str.isascii() and bed_str.isdigit()):
            raise ValueError("bed number must be a whole number")
        bed_num = int(bed_str)
        if not 1 <= bed_num <= 999:
            raise ValueError("bed number must be between 1 and 999")
    except ValueError as e:
        return f"Invalid input: {e}"

    return f"{WARD_NAMES[ward]} Bed #{bed_num}"


def main():
    print("==== Running parse_vitals_summary ====")
    v_input = input("Enter vitals (HR,SpO2,Temp): ")
    print("Summary:", parse_vitals_summary(v_input))

    print("\n==== Running compute_patient_bmi ====")
    b_input = input("Enter weight/height (e.g. 70/1.75): ")
    print("BMI:", compute_patient_bmi(b_input))

    print("\n==== Running assign_ward_bed ====")
    w_input = input("Enter allocation (e.g. ICU-05): ")
    print("Assignment:", assign_ward_bed(w_input))


if __name__ == "__main__":
    main()
