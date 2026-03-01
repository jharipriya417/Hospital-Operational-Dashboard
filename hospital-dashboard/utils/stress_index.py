import pandas as pd


DEPARTMENT_WEIGHTS = {
    "ICU":       {"patient_staff_ratio": 0.35, "emergency_ratio": 0.40, "bed_utilization": 0.25},
    "Emergency": {"patient_staff_ratio": 0.25, "emergency_ratio": 0.50, "bed_utilization": 0.25},
    "OPD":       {"patient_staff_ratio": 0.45, "emergency_ratio": 0.15, "bed_utilization": 0.40},
    "Radiology": {"patient_staff_ratio": 0.40, "emergency_ratio": 0.20, "bed_utilization": 0.40},
    "Surgery":   {"patient_staff_ratio": 0.35, "emergency_ratio": 0.30, "bed_utilization": 0.35},
}

DEFAULT_WEIGHTS = {"patient_staff_ratio": 0.35, "emergency_ratio": 0.30, "bed_utilization": 0.35}

STRESS_THRESHOLDS = {"stable": 40, "watch": 70}


def calculate_stress_index(row: pd.Series) -> dict:
    dept = row.get("department", "Unknown")
    weights = DEPARTMENT_WEIGHTS.get(dept, DEFAULT_WEIGHTS)

    # Patient-to-staff ratio score (normalized 0-100)
    staff = max(row.get("staff_available", 1), 1)
    patients = row.get("patients_admitted", 0)
    patient_staff_ratio = patients / staff
    # Benchmark: ratio > 10 = full stress for most depts
    ps_score = min((patient_staff_ratio / 10) * 100, 100)

    # Emergency case ratio score
    total_patients = max(patients, 1)
    emergency_cases = row.get("emergency_cases", 0)
    emergency_ratio = emergency_cases / total_patients
    # Benchmark: ratio > 0.8 = full stress
    em_score = min((emergency_ratio / 0.8) * 100, 100)

    # Bed utilization score
    beds_total = max(row.get("beds_total", 1), 1)
    beds_occupied = row.get("beds_occupied", 0)
    bed_util = beds_occupied / beds_total
    # Benchmark: >90% utilization = full stress
    bed_score = min((bed_util / 0.9) * 100, 100)

    stress_index = (
        weights["patient_staff_ratio"] * ps_score
        + weights["emergency_ratio"] * em_score
        + weights["bed_utilization"] * bed_score
    )
    stress_index = round(stress_index, 2)

    if stress_index <= STRESS_THRESHOLDS["stable"]:
        status = "Stable"
        status_class = "stable"
    elif stress_index <= STRESS_THRESHOLDS["watch"]:
        status = "Under Watch"
        status_class = "watch"
    else:
        status = "Critical"
        status_class = "critical"

    return {
        "department": dept,
        "stress_index": stress_index,
        "status": status,
        "status_class": status_class,
        "ps_score": round(ps_score, 2),
        "em_score": round(em_score, 2),
        "bed_score": round(bed_score, 2),
    }


def get_department_stress(df: pd.DataFrame) -> list[dict]:
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date]
    results = []
    for _, row in latest_df.iterrows():
        results.append(calculate_stress_index(row))
    return sorted(results, key=lambda x: x["stress_index"], reverse=True)


def get_stress_trend(df: pd.DataFrame, department: str) -> list[dict]:
    dept_df = df[df["department"] == department].copy()
    dept_df = dept_df.sort_values("date")
    trend = []
    for _, row in dept_df.iterrows():
        result = calculate_stress_index(row)
        result["date"] = str(row["date"])
        trend.append(result)
    return trend
