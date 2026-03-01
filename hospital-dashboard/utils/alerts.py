import pandas as pd
from utils.stress_index import calculate_stress_index, STRESS_THRESHOLDS


ALERT_LEVELS = {
    "critical": {"icon": "🔴", "label": "CRITICAL", "priority": 1},
    "warning":  {"icon": "🟡", "label": "WARNING",  "priority": 2},
    "info":     {"icon": "🔵", "label": "INFO",     "priority": 3},
}


def _make_alert(level: str, category: str, department: str, message: str, value=None) -> dict:
    return {
        "level": level,
        "icon": ALERT_LEVELS[level]["icon"],
        "label": ALERT_LEVELS[level]["label"],
        "priority": ALERT_LEVELS[level]["priority"],
        "category": category,
        "department": department,
        "message": message,
        "value": value,
    }


def generate_alerts(df: pd.DataFrame) -> list[dict]:
    alerts = []
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date]

    dates_sorted = sorted(df["date"].unique())
    prev_date = dates_sorted[-2] if len(dates_sorted) >= 2 else None
    prev_df = df[df["date"] == prev_date] if prev_date else None

    for _, row in latest_df.iterrows():
        dept = row["department"]
        stress = calculate_stress_index(row)

        # --- Stress index alerts ---
        if stress["stress_index"] > STRESS_THRESHOLDS["watch"]:
            alerts.append(_make_alert(
                "critical", "Stress Index", dept,
                f"{dept} is in CRITICAL stress (index: {stress['stress_index']}). Immediate intervention required.",
                stress["stress_index"]
            ))
        elif stress["stress_index"] > STRESS_THRESHOLDS["stable"]:
            alerts.append(_make_alert(
                "warning", "Stress Index", dept,
                f"{dept} is Under Watch (index: {stress['stress_index']}). Monitor closely.",
                stress["stress_index"]
            ))

        # --- Bed occupancy alerts ---
        beds_total = max(row.get("beds_total", 1), 1)
        beds_occupied = row.get("beds_occupied", 0)
        bed_util_pct = (beds_occupied / beds_total) * 100
        if bed_util_pct >= 100:
            alerts.append(_make_alert(
                "critical", "Bed Capacity", dept,
                f"{dept} has reached FULL bed capacity ({beds_occupied}/{beds_total} beds occupied).",
                round(bed_util_pct, 1)
            ))
        elif bed_util_pct >= 90:
            alerts.append(_make_alert(
                "warning", "Bed Capacity", dept,
                f"{dept} bed utilization is at {bed_util_pct:.1f}% ({beds_occupied}/{beds_total} beds).",
                round(bed_util_pct, 1)
            ))

        # --- Staff shortage alerts ---
        staff_available = row.get("staff_available", 0)
        staff_required = row.get("staff_required", 0)
        if staff_required > 0:
            staff_coverage = (staff_available / staff_required) * 100
            if staff_coverage < 70:
                alerts.append(_make_alert(
                    "critical", "Staff Shortage", dept,
                    f"{dept} has severe staff shortage: {staff_available} available vs {staff_required} required ({staff_coverage:.0f}% coverage).",
                    round(staff_coverage, 1)
                ))
            elif staff_coverage < 85:
                alerts.append(_make_alert(
                    "warning", "Staff Shortage", dept,
                    f"{dept} staff coverage is low: {staff_available}/{staff_required} ({staff_coverage:.0f}%).",
                    round(staff_coverage, 1)
                ))

        # --- Pending cases backlog alerts ---
        pending = row.get("pending_cases", 0)
        admitted = max(row.get("patients_admitted", 1), 1)
        backlog_ratio = pending / admitted
        if backlog_ratio > 1.5:
            alerts.append(_make_alert(
                "critical", "Case Backlog", dept,
                f"{dept} has a critical backlog: {pending} pending cases vs {admitted} admitted today.",
                pending
            ))
        elif backlog_ratio > 0.8:
            alerts.append(_make_alert(
                "warning", "Case Backlog", dept,
                f"{dept} backlog is building up: {pending} pending cases.",
                pending
            ))

        # --- Emergency surge alerts ---
        emergency = row.get("emergency_cases", 0)
        if prev_df is not None:
            prev_row = prev_df[prev_df["department"] == dept]
            if not prev_row.empty:
                prev_emergency = prev_row.iloc[0].get("emergency_cases", 0)
                if prev_emergency > 0:
                    change_pct = ((emergency - prev_emergency) / prev_emergency) * 100
                    if change_pct >= 20:
                        alerts.append(_make_alert(
                            "critical", "Emergency Surge", dept,
                            f"{dept} emergency cases surged by {change_pct:.1f}% since yesterday ({prev_emergency} → {emergency}).",
                            round(change_pct, 1)
                        ))
                    elif change_pct >= 10:
                        alerts.append(_make_alert(
                            "warning", "Emergency Surge", dept,
                            f"{dept} emergency cases rose by {change_pct:.1f}% since yesterday.",
                            round(change_pct, 1)
                        ))

        # --- Resolution time alerts ---
        avg_res = row.get("avg_resolution_time_hrs", 0)
        if dept == "OPD" and avg_res > 3.0:
            alerts.append(_make_alert(
                "warning", "Resolution Time", dept,
                f"OPD average resolution time is elevated at {avg_res:.1f} hrs (target: <3 hrs).",
                avg_res
            ))
        elif dept == "Emergency" and avg_res > 5.0:
            alerts.append(_make_alert(
                "critical", "Resolution Time", dept,
                f"Emergency average resolution time is critically high at {avg_res:.1f} hrs.",
                avg_res
            ))

    alerts.sort(key=lambda x: x["priority"])
    return alerts


def get_alert_summary(alerts: list[dict]) -> dict:
    return {
        "total": len(alerts),
        "critical": sum(1 for a in alerts if a["level"] == "critical"),
        "warning": sum(1 for a in alerts if a["level"] == "warning"),
        "info": sum(1 for a in alerts if a["level"] == "info"),
    }
