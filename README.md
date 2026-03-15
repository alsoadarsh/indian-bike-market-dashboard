# Indian Bike Market Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Dash](https://img.shields.io/badge/Dash-2.0+-orange)
![Plotly](https://img.shields.io/badge/Plotly-5.0+-brightgreen)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

---

## What It Does

An interactive analytics dashboard for the Indian two-wheeler market — pricing,
mileage, brand share, and fuel type distribution across 10,000+ records.

Built with Python Dash and Plotly. Every chart, KPI, and analytics panel
updates live as filters change.

> Dataset: [Indian Bike Sales Dataset](https://www.kaggle.com/datasets/ak0212/indian-bike-sales-dataset) · Kaggle (ak0212) · Synthetic data used for demonstration.

---

## Dashboard Overview

![Dashboard](docs/screenshots/dashboard_overview.png)

---

## Features

**Left sidebar — all filters, all controls:**
- Price range slider
- Fuel type dropdown
- Brand checklist (top 10 brands, 6 selected by default)
- Model checklist — chained from brand: pick a brand, only its models appear

**Analysis modes** (toggle in sidebar):
- Financial — average price
- Market — model count / volume
- Performance — mileage efficiency

**Four charts, all filter-aware:**

| Chart | What It Shows |
|-------|--------------|
| Price vs Mileage scatter | Price–efficiency relationship by fuel type, live trend line and R² |
| Brand Market Share | Share of top 8 brands in the current filtered view |
| Engine Capacity Trends | Price, mileage, or volume by engine size — dual axis with volume overlay |
| Fuel Type Analysis | Avg price / mileage / count per brand, grouped by fuel type |

**Analytics panel** — 5 tabs that recompute on every filter change:

| Tab | What It Computes |
|-----|-----------------|
| Overview | Total models, HHI market concentration, avg price, dominant fuel |
| Scatter | Live correlation coefficient, quadrant breakdown |
| Brands | Market leader share, top-3 concentration, market structure |
| Engine | Dominant displacement, price or mileage gap across engine sizes |
| Fuel | Powertrain mix, EV brand count, electric vs petrol price premium |

**Zoom modals** — ⤢ button on each chart opens a full-screen expanded view

**KPI cards** — Total Bikes, Avg Price, Leading Brand, Active Brands — all filter-aware including model selection

**Key Findings (computed from data at startup, not hardcoded):**

| Finding | Method |
|---------|--------|
| Price–mileage correlation | Pearson r across full dataset |
| Highest avg price — fuel type | groupby().mean().idxmax() |
| Best mileage — fuel type | groupby().mean().idxmax() |
| Best resale retention | mean(Resale Price / Price) by brand |

---

## Screenshots

**Price vs Mileage with Trend Line**
![Scatter](docs/screenshots/scatter_trend.png)

---

## Project Structure

```
indian-bike-market-dashboard/
├── app.py                   ← run this
├── requirements.txt
├── .gitignore
├── README.md
└── docs/
    └── screenshots/
        ├── dashboard_overview.png
        └── scatter_trend.png
```

Dataset (`bike_sales.xlsx`) is not tracked — see Setup below.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/indian-bike-market-dashboard
cd indian-bike-market-dashboard
pip install -r requirements.txt
```

### 2. Get the data

Download from Kaggle:
https://www.kaggle.com/datasets/ak0212/indian-bike-sales-dataset

Rename the file to `bike_sales.xlsx` and place it in the project root.

Expected columns:

| Column | Type |
|--------|------|
| Brand | String |
| Model | String |
| Price (INR) | Numeric |
| Engine Capacity (cc) | Numeric |
| Fuel Type | String |
| Mileage (km/l) | Numeric |
| Resale Price (INR) | Numeric (optional) |

### 3. Run

```bash
python app.py
```

Open http://localhost:8061

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: dash_bootstrap_components` | `pip install dash-bootstrap-components` |
| `FileNotFoundError: bike_sales.xlsx` | Place the file in the same folder as `app.py` |
| Resale finding shows N/A | Dataset missing `Resale Price (INR)` column — rest of app still works |
| Port in use | Change `port=8061` at the bottom of `app.py` |
| Blank charts | Column name mismatch — names are case-sensitive |

---

## Tech Stack

Python · Dash · Plotly · Pandas · NumPy · SciPy · dash-bootstrap-components · openpyxl

---

## Author

**Adarsh Shukla**
MS Business Analytics · University of Dayton
[LinkedIn](https://linkedin.com/in/adarshhshukla) · [GitHub](https://github.com/alsoadarsh)
