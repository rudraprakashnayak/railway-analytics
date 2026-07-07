# Indian Railways Analytics Dashboard

An interactive Streamlit dashboard for exploring Indian Railways train schedules, delay patterns, and performance metrics. Built with synthetic data resembling real Indian Railways operations.

> Pure analytics & visualization — no machine learning.

**[Live Demo]** _(link after deployment)_

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data Processing | pandas, numpy |
| Database | SQLite3 |
| Dashboard | Streamlit |
| Charts | Plotly (interactive) |

---

## Features

- **KPI Dashboard** — Total trains, average delay, on-time %, active routes
- **Interactive Filters** — Date range, train type, route, season
- **Delay Trend Analysis** — Monthly delay trends and train volume charts
- **Route Analysis** — Top 15 most delayed and busiest routes
- **Distribution Charts** — Train type breakdown, delay category donut, delay histogram
- **Seasonal Heatmap** — Delay patterns by season x day of week
- **Data Explorer** — Full searchable data table with CSV download
- **10 SQL Analytics Queries** — Busiest routes, avg delay by type, monthly trends, on-time %, seasonal patterns, day-of-week analysis, and more
- **Automated Data Pipeline** — Generate, clean, and refresh scripts
- **SQLite Database** — Proper schema with indexes for fast queries

---

## Project Structure

```
railway-analytics/
├── app.py                      # Streamlit dashboard
├── requirements.txt            # Python dependencies
├── .gitignore
├── README.md
├── data/
│   ├── raw_trains.csv          # Raw synthetic dataset (5,500+ records)
│   ├── clean_trains.csv        # Cleaned dataset
│   └── railway.db              # SQLite database
└── scripts/
    ├── generate_data.py        # Synthetic data generator
    ├── clean_data.py           # Data cleaning + SQLite loader + SQL queries
    └── refresh_data.py         # Automation script for scheduled refresh
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/railway-analytics.git
cd railway-analytics
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate data (if not included)

```bash
python scripts/generate_data.py
python scripts/clean_data.py
```

### 4. Launch the dashboard

```bash
streamlit run app.py
```

The app opens at **https://railway-analytics-mjdxubhsqtcyzozqps2ro9.streamlit.app/**.

> The dashboard auto-generates data on first run if the database doesn't exist.

---

## Data Refresh

Simulate a scheduled refresh with new records:

```bash
python scripts/refresh_data.py              # adds 200 records
python scripts/refresh_data.py --records 500  # custom count
```

---

## Screenshots

> Add screenshots after deployment

| View | Description |
|:----:|:-----------:|
| ![KPI Cards](screenshots/kpi_cards.png) | Top KPI cards |
| ![Delay Trends](screenshots/delay_trends.png) | Monthly delay trend |
| ![Route Analysis](screenshots/route_analysis.png) | Top delayed routes |
| ![Heatmap](screenshots/heatmap.png) | Seasonal delay heatmap |

---

## Live Demo

**Streamlit Community Cloud**: _[Add your deployed app URL here]_

---

## Notes

- All data is **synthetic** — generated to resemble real Indian Railways patterns
- No ML/prediction features — purely descriptive analytics
- Dataset includes intentional data quality issues for the cleaning pipeline to demonstrate

---

## License

Educational and portfolio project.
