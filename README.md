# PowerPulse — Residential Energy Consumption Analytics

> End-to-end data analytics project on ~2 million rows of household smart-meter
> data. From raw `.txt` → cleaned SQL database → trend analysis → time-of-use
> tariff model → recurring Excel report → interactive Streamlit dashboard.

![Dashboard screenshot](reports/figures/dashboard_full.png)

## The question

Could a household save real money by shifting *when* it uses electricity — and how
much, exactly? Using four years of minute-level smart-meter readings from a French
household, this project answers that with a quantified, validated number.

## Headline findings

- **The household consumes ~9700 kWh per year**, peaking in the evening
  (6–9pm) and in winter.
- **The water-heater / AC circuit is the single largest measured load** —
  ~35.5% of metered consumption.
- **Switching to a time-of-use tariff is *more expensive* today** because the
  evening peak dominates. But if ~50% of the water-heater circuit's peak-hour
  energy is shifted off-peak (a timer is enough), the household saves
  ~**€111/year** at illustrative tariff rates — a result that holds
  consistently across three independent full years of data.

## Tech stack

**Python** (pandas, NumPy, matplotlib, SQLAlchemy, openpyxl, Streamlit) ·
**SQL** (SQLite) · **Excel** · **Jupyter** · **Git**

## Repository

| Path | What's in it |
|---|---|
| `sql/` | Schema, data-load script, analysis queries |
| `notebooks/` | Cleaning & validation, exploratory analysis, business analysis |
| `reports/build_monthly_report.py` | Recurring monthly Excel report generator |
| `reports/figures/` | Chart images used in this README |
| `app/dashboard.py` | Interactive Streamlit dashboard |
| `PROJECT_GUIDE.md` | Project rationale, scope, and phase-by-phase roadmap |

## Selected charts

| | |
|---|---|
| ![Load curve](reports/figures/load_curve_by_hour.png) | ![Monthly trend](reports/figures/monthly_energy_trend.png) |
| Average power by hour of day — clear evening peak | Total energy by month — strong winter seasonality |

## How to run it

```bash
# 1. Clone and enter
git clone https://github.com/WaseemAttari00/powerpulse.git
cd powerpulse

# 2. Set up the environment
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt

# 3. Get the data
#    Download "Individual Household Electric Power Consumption" from the UCI ML
#    Repository (dataset #235) and place household_power_consumption.txt in data/raw/.

# 4. Build the SQL database
python sql/load_data.py

# 5. Run the analysis (open in VS Code or Jupyter)
notebooks/01_cleaning_and_validation.ipynb
notebooks/02_exploratory_analysis.ipynb
notebooks/03_business_analysis.ipynb

# 6. Generate the monthly report
python reports/build_monthly_report.py 2008-03

# 7. Launch the dashboard
streamlit run app/dashboard.py
```

## Data quality & validation

This project takes data accuracy seriously. The cleaning notebook documents every
issue found and the decision made about it — including a sub-metering reconciliation
check that compares the household total against the three sub-meters to confirm the
data is internally consistent. See `notebooks/01_cleaning_and_validation.ipynb` for
the full data quality log.

## About this project

Built as a portfolio piece for a Data Analyst role by an Electrical & Computer
Engineering student. The energy-and-metering subject matter ties to the ECE
domain; the SQL / Python / Excel / dashboard stack maps to a typical analyst job.

Plain-language summary of findings: see [`reports/findings_summary.md`](reports/findings_summary.md).