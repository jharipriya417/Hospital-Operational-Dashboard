import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify
from utils.stress_index import get_department_stress, get_stress_trend
from utils.alerts import generate_alerts, get_alert_summary
from utils.predictor import predict_next_day, get_workload_forecast_chart

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "hospital_data.csv")


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df["date"] = df["date"].dt.date
    return df


def get_kpi_summary(df: pd.DataFrame) -> dict:
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date]

    total_patients   = int(latest["patients_admitted"].sum())
    total_discharged = int(latest["patients_discharged"].sum())
    total_pending    = int(latest["pending_cases"].sum())
    total_emergency  = int(latest["emergency_cases"].sum())
    total_beds       = int(latest["beds_total"].sum())
    total_occupied   = int(latest["beds_occupied"].sum())
    total_staff      = int(latest["staff_available"].sum())
    total_required   = int(latest["staff_required"].sum())
    avg_resolution   = round(float(latest["avg_resolution_time_hrs"].mean()), 1)

    bed_util_pct     = round((total_occupied / max(total_beds, 1)) * 100, 1)
    staff_cov_pct    = round((total_staff / max(total_required, 1)) * 100, 1)

    return {
        "date":             str(latest_date),
        "total_patients":   total_patients,
        "total_discharged": total_discharged,
        "total_pending":    total_pending,
        "total_emergency":  total_emergency,
        "total_beds":       total_beds,
        "total_occupied":   total_occupied,
        "bed_util_pct":     bed_util_pct,
        "total_staff":      total_staff,
        "total_required":   total_required,
        "staff_cov_pct":    staff_cov_pct,
        "avg_resolution":   avg_resolution,
    }


def get_department_overview(df: pd.DataFrame) -> list[dict]:
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date]
    overview = []
    for _, row in latest.iterrows():
        bed_util = round((row["beds_occupied"] / max(row["beds_total"], 1)) * 100, 1)
        staff_cov = round((row["staff_available"] / max(row["staff_required"], 1)) * 100, 1)
        overview.append({
            "department":       row["department"],
            "patients_admitted": int(row["patients_admitted"]),
            "pending_cases":    int(row["pending_cases"]),
            "emergency_cases":  int(row["emergency_cases"]),
            "bed_util_pct":     bed_util,
            "staff_cov_pct":    staff_cov,
            "avg_resolution":   round(float(row["avg_resolution_time_hrs"]), 1),
        })
    return sorted(overview, key=lambda x: x["patients_admitted"], reverse=True)


def get_trend_data(df: pd.DataFrame) -> dict:
    departments = df["department"].unique().tolist()
    dates = sorted([str(d) for d in df["date"].unique()])

    patient_trends = {}
    emergency_trends = {}
    pending_trends = {}

    for dept in departments:
        dept_df = df[df["department"] == dept].sort_values("date")
        patient_trends[dept]   = dept_df["patients_admitted"].tolist()
        emergency_trends[dept] = dept_df["emergency_cases"].tolist()
        pending_trends[dept]   = dept_df["pending_cases"].tolist()

    return {
        "dates":            dates,
        "departments":      departments,
        "patient_trends":   patient_trends,
        "emergency_trends": emergency_trends,
        "pending_trends":   pending_trends,
    }


def get_resolution_data(df: pd.DataFrame) -> dict:
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date]
    return {
        "departments":    latest["department"].tolist(),
        "resolution_hrs": [round(float(v), 1) for v in latest["avg_resolution_time_hrs"].tolist()],
        "pending_cases":  latest["pending_cases"].tolist(),
        "completed":      latest["patients_discharged"].tolist(),
    }


@app.route("/")
def dashboard():
    df = load_data()
    kpi         = get_kpi_summary(df)
    dept_stress = get_department_stress(df)
    alerts      = generate_alerts(df)
    alert_summary = get_alert_summary(alerts)
    predictions = predict_next_day(df)
    dept_overview = get_department_overview(df)

    return render_template(
        "dashboard.html",
        kpi=kpi,
        dept_stress=dept_stress,
        alerts=alerts[:10],
        alert_summary=alert_summary,
        predictions=predictions,
        dept_overview=dept_overview,
    )


@app.route("/api/trends")
def api_trends():
    df = load_data()
    return jsonify(get_trend_data(df))


@app.route("/api/resolution")
def api_resolution():
    df = load_data()
    return jsonify(get_resolution_data(df))


@app.route("/api/stress-trend/<department>")
def api_stress_trend(department):
    df = load_data()
    trend = get_stress_trend(df, department)
    return jsonify(trend)


@app.route("/api/forecast")
def api_forecast():
    df = load_data()
    return jsonify(get_workload_forecast_chart(df))


@app.route("/api/kpi")
def api_kpi():
    df = load_data()
    return jsonify(get_kpi_summary(df))


@app.route("/api/alerts")
def api_alerts():
    df = load_data()
    alerts = generate_alerts(df)
    return jsonify({
        "alerts": alerts,
        "summary": get_alert_summary(alerts),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
