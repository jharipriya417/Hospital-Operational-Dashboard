# Hospital Operational Intelligence Dashboard

An Administrative Analytics Dashboard that transforms hospital operational data into actionable intelligence for administrators.

## Features

- **Operational Monitoring** — Real-time KPIs: patient volume, bed occupancy, staff coverage, emergency load
- **Department Stress Index** — Composite score (patient/staff ratio + emergency load + bed utilization) with Stable / Under Watch / Critical classification
- **Smart Alerts** — Automated detection of staff shortages, bed overcapacity, emergency surges, and case backlogs
- **Trend Analysis** — 28-day historical charts for admissions, emergency cases, and pending workload
- **Predictive Forecasting** — Next-day workload estimates using linear trend regression with department-level risk ratings
- **Administrative Awareness Panel** — Consolidated status view for rapid situational awareness

## Project Structure

```
hospital-dashboard/
├── app.py                  # Flask application & API routes
├── data/
│   └── hospital_data.csv   # 28-day operational dataset (5 departments)
├── templates/
│   └── dashboard.html      # Single-page dashboard UI
├── static/
│   ├── style.css           # Dark-theme responsive styling
│   └── charts.js           # Chart.js chart rendering & navigation
├── utils/
│   ├── __init__.py
│   ├── stress_index.py     # Stress index calculation engine
│   ├── alerts.py           # Alert generation logic
│   └── predictor.py        # Workload prediction engine
└── README.md
```

## Setup & Run

### 1. Install dependencies

```bash
pip install flask pandas numpy
```

### 2. Run the application

```bash
cd hospital-dashboard
python app.py
```

### 3. Open in browser

```
http://localhost:5000
```

## Departments Covered

| Department | Focus |
|---|---|
| ICU | Critical care, high staff-to-patient sensitivity |
| OPD | High patient volume, throughput efficiency |
| Emergency | Emergency surge detection, response time |
| Radiology | Equipment/bed utilization, case throughput |
| Surgery | Resolution time, critical case load |

## Stress Index Formula

```
Stress Index = w1 × PatientStaffScore + w2 × EmergencyScore + w3 × BedUtilizationScore
```

Weights are department-specific (e.g., Emergency weights emergency load at 50%).

| Status | Score Range |
|---|---|
| Stable | 0 – 40 |
| Under Watch | 41 – 70 |
| Critical | 71 – 100 |

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Main dashboard |
| `GET /api/trends` | 28-day trend data for all departments |
| `GET /api/resolution` | Resolution time and pending cases |
| `GET /api/stress-trend/<dept>` | Stress index trend for a department |
| `GET /api/forecast` | 7-day history + 3-day forecast |
| `GET /api/kpi` | Current KPI summary |
| `GET /api/alerts` | Active alerts and summary |
