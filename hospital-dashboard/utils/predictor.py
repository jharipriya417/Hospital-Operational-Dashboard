import pandas as pd
import numpy as np
from utils.stress_index import calculate_stress_index, STRESS_THRESHOLDS


def _linear_trend(values: list[float]) -> float:
    """Return the next predicted value using simple linear regression."""
    if len(values) < 2:
        return values[-1] if values else 0
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    coeffs = np.polyfit(x, y, 1)
    return float(np.polyval(coeffs, len(values)))


def _weighted_average(values: list[float], decay: float = 0.85) -> float:
    """Exponentially weighted average giving more weight to recent values."""
    if not values:
        return 0.0
    weights = [decay ** i for i in range(len(values) - 1, -1, -1)]
    total_weight = sum(weights)
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def predict_next_day(df: pd.DataFrame) -> list[dict]:
    departments = df["department"].unique()
    predictions = []

    for dept in departments:
        dept_df = df[df["department"] == dept].sort_values("date")

        # Use last 7 days for prediction
        recent = dept_df.tail(7)

        admitted_vals    = recent["patients_admitted"].tolist()
        emergency_vals   = recent["emergency_cases"].tolist()
        pending_vals     = recent["pending_cases"].tolist()
        staff_vals       = recent["staff_available"].tolist()
        bed_occ_vals     = recent["beds_occupied"].tolist()
        resolution_vals  = recent["avg_resolution_time_hrs"].tolist()

        pred_admitted   = max(0, round(_linear_trend(admitted_vals)))
        pred_emergency  = max(0, round(_linear_trend(emergency_vals)))
        pred_pending    = max(0, round(_linear_trend(pending_vals)))
        pred_staff      = max(1, round(_weighted_average(staff_vals)))
        pred_bed_occ    = max(0, round(_linear_trend(bed_occ_vals)))
        pred_resolution = max(0.5, round(_linear_trend(resolution_vals), 1))

        latest_row = dept_df.iloc[-1]
        beds_total = int(latest_row.get("beds_total", 1))
        staff_required = int(latest_row.get("staff_required", 1))

        # Clamp bed occupancy to total
        pred_bed_occ = min(pred_bed_occ, beds_total)

        # Build a synthetic row for stress calculation
        synthetic_row = pd.Series({
            "department":             dept,
            "patients_admitted":      pred_admitted,
            "emergency_cases":        pred_emergency,
            "staff_available":        pred_staff,
            "beds_total":             beds_total,
            "beds_occupied":          pred_bed_occ,
        })
        stress = calculate_stress_index(synthetic_row)

        bed_util_pct = round((pred_bed_occ / max(beds_total, 1)) * 100, 1)
        staff_coverage_pct = round((pred_staff / max(staff_required, 1)) * 100, 1)

        # Determine risk level
        if stress["stress_index"] > STRESS_THRESHOLDS["watch"]:
            risk_level = "High Risk"
            risk_class = "critical"
        elif stress["stress_index"] > STRESS_THRESHOLDS["stable"]:
            risk_level = "Moderate Risk"
            risk_class = "watch"
        else:
            risk_level = "Low Risk"
            risk_class = "stable"

        # Generate recommendation
        recommendations = []
        if staff_coverage_pct < 80:
            recommendations.append(f"Schedule additional staff (coverage at {staff_coverage_pct}%)")
        if bed_util_pct >= 90:
            recommendations.append(f"Prepare overflow capacity (beds at {bed_util_pct}%)")
        if pred_emergency > latest_row.get("emergency_cases", 0) * 1.15:
            recommendations.append("Increase emergency team readiness")
        if pred_pending > pred_admitted * 1.2:
            recommendations.append("Prioritize backlog clearance")
        if not recommendations:
            recommendations.append("Operations expected to remain stable")

        predictions.append({
            "department":          dept,
            "predicted_patients":  pred_admitted,
            "predicted_emergency": pred_emergency,
            "predicted_pending":   pred_pending,
            "predicted_staff":     pred_staff,
            "predicted_bed_occ":   pred_bed_occ,
            "bed_util_pct":        bed_util_pct,
            "staff_coverage_pct":  staff_coverage_pct,
            "predicted_resolution_hrs": pred_resolution,
            "predicted_stress":    stress["stress_index"],
            "risk_level":          risk_level,
            "risk_class":          risk_class,
            "recommendations":     recommendations,
        })

    return sorted(predictions, key=lambda x: x["predicted_stress"], reverse=True)


def get_workload_forecast_chart(df: pd.DataFrame) -> dict:
    """Return 7-day historical + 3-day forecast data per department for charting."""
    departments = df["department"].unique()
    forecast_data = {}

    for dept in departments:
        dept_df = df[df["department"] == dept].sort_values("date")
        recent = dept_df.tail(7)
        admitted_vals = recent["patients_admitted"].tolist()
        dates = [str(d) for d in recent["date"].tolist()]

        # Forecast next 3 days
        forecast_vals = []
        temp_vals = admitted_vals.copy()
        for _ in range(3):
            next_val = max(0, round(_linear_trend(temp_vals)))
            forecast_vals.append(next_val)
            temp_vals.append(next_val)

        forecast_data[dept] = {
            "historical_dates":  dates,
            "historical_values": admitted_vals,
            "forecast_values":   forecast_vals,
        }

    return forecast_data
