# PowerPulse — Residential Energy Consumption Analytics & Reporting

A portfolio data-analytics project for an Electrical & Computer Engineering student
targeting a Data Analyst role. Built with **SQL + Python + Excel**.

---

## 1. Why this project

The job description asks for six things. This project is deliberately designed so that
every phase produces evidence for one or more of them:

| What the employer wants | How this project shows it |
|---|---|
| SQL / Python / Excel tied to real work | Data is loaded and queried in SQL, cleaned and analyzed in Python, and a recurring report is built in Excel |
| End-to-end data workflow (collect → clean → trend → use) | The phases below literally follow that arc |
| Dashboards & recurring reports for leadership | Phase 5 (Excel monthly report) and Phase 6 (interactive dashboard/app) |
| Communicating with non-technical stakeholders | The "household energy bill" framing is universally understood; deliverables include a plain-language summary |
| Data accuracy, validation, quality control | Phase 2 is a genuine reconciliation exercise — the dataset has missing values and a measurable gap between total power and sub-metered power |
| Business impact & process improvement | Phase 4 quantifies peak-demand cost and models a "what-if" savings scenario |

It also ties directly to your ECE background: power, energy, load profiles, metering,
peak demand, and time-of-use are all core electrical engineering concepts. In an
interview you can speak about both the *analytics* and the *domain* credibly — that
combination is what makes a candidate stand out.

---

## 2. The dataset

**Individual Household Electric Power Consumption** — UCI Machine Learning Repository.

- One household near Paris, sampled every minute for ~4 years (Dec 2006 – Nov 2010).
- ~2,075,259 rows. Large enough to be realistic, small enough to run on a laptop.
- Columns: `Date`, `Time`, `Global_active_power` (kW), `Global_reactive_power` (kW),
  `Voltage` (V), `Global_intensity` (A), and three `Sub_metering_1/2/3` channels (Wh):
  kitchen, laundry room, and water-heater/AC.
- Why it is good for *this* project specifically:
  - It has **real missing data** (gaps marked `?`) — a true cleaning task, not a toy.
  - It supports a **reconciliation check**: the three sub-meters should account for a
    portion of total active power, and the "unmeasured remainder" can be computed and
    sanity-checked. That is your data-quality story.
  - It is a **time series**, so it naturally produces trends, seasonality, peak-demand
    analysis, and recurring monthly reports.

Download page: search "UCI Individual household electric power consumption". The file
is a single `.txt` (semicolon-separated), about 130 MB unzipped.

> Alternative if you want a different flavor: UCI "SECOM" semiconductor manufacturing
> yield data is even more ECE-flavored and very strong on the data-quality angle, but
> it is wide (590 sensors) and leans toward machine learning. The energy dataset gives
> you a cleaner end-to-end analyst story. Stick with energy unless you specifically
> want an ML emphasis.

---

## 3. The business framing

Pretend you are an analyst at a utility company or a smart-home energy startup. Your
stakeholders are an operations team and a non-technical leadership team. The questions
you are answering:

1. **When does this household use the most power?** (hour of day, day of week, season)
2. **What is driving consumption?** (which sub-metered circuits, and the unmeasured rest)
3. **What would peak-demand or time-of-use pricing cost this household**, and how much
   could shifting load save them?
4. **Can we trust the meter data?** (missing intervals, reconciliation gap, outliers)
5. **What should a monthly energy report to leadership contain**, and can it be
   regenerated automatically each month?

Keep these five questions written at the top of your notebook. Every chart you make
should answer one of them — that discipline is what separates a portfolio piece from
a pile of plots.

---

## 4. Deliverables (your GitHub repo)

```
powerpulse/
├── README.md                  # the front door — narrative + screenshots + findings
├── data/
│   ├── raw/                    # original download (gitignored — too big)
│   └── processed/              # cleaned parquet/CSV
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_load_data.sql
│   └── 03_analysis_queries.sql
├── notebooks/
│   ├── 01_cleaning_and_validation.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   └── 03_business_analysis.ipynb
├── reports/
│   ├── monthly_energy_report.xlsx   # the recurring Excel report
│   └── findings_summary.md          # 1-page plain-language writeup for "leadership"
├── app/
│   └── dashboard.py                 # Streamlit dashboard
└── requirements.txt
```

A reviewer should be able to read the README and understand the whole story in three
minutes without running anything. Everything else is supporting evidence.

---

## 5. Phase-by-phase roadmap

Each phase below has a **goal**, the **skills it demonstrates**, and **what to produce**.
Detailed step-by-step instructions for each phase will be delivered as you work through
them — this document is the map, not the full walkthrough.

### Phase 0 — Setup
**Goal:** a clean repo and working environment.
**Produce:** Git repo, virtual environment, `requirements.txt` (pandas, numpy,
matplotlib, seaborn, jupyter, sqlalchemy, streamlit, openpyxl), a database (start with
SQLite — zero setup, real SQL), and a `.gitignore` that excludes the raw data.

### Phase 1 — Data acquisition & loading into SQL
**Goal:** get the raw data into a queryable SQL table.
**Skills:** SQL schema design, bulk loading, type handling.
**Produce:** `01_create_schema.sql`, a load script, and a first `SELECT COUNT(*)` /
`SELECT ... LIMIT 10` sanity check. Decide how to store `Date`+`Time` (combine into a
single timestamp column — you will thank yourself later).

### Phase 2 — Data cleaning & validation (your QC story)
**Goal:** turn raw data into trustworthy data, and *document what was wrong*.
**Skills:** missing-data handling, outlier detection, reconciliation logic.
**Produce:** `01_cleaning_and_validation.ipynb` that:
- quantifies missing rows (how many minutes have no reading, and when they cluster);
- handles the `?` values explicitly (don't silently drop — decide and justify);
- checks physical plausibility (voltage near 230–250 V, non-negative power);
- computes the **reconciliation gap**: `Global_active_power` converted to Wh per
  minute, minus the sum of the three sub-meters — the "unmetered" remainder. Confirm
  it is positive and reasonably stable. This single check is the most interview-worthy
  thing in the whole project: it is exactly "caught a reporting issue / improved data
  integrity."
- A short **data quality log** (a markdown cell or table): issue found → decision made
  → impact.

### Phase 3 — Exploratory analysis & trend finding
**Goal:** find the real patterns.
**Skills:** SQL aggregation (GROUP BY hour/day/month), Python visualization.
**Produce:** `02_exploratory_analysis.ipynb` and `03_analysis_queries.sql`. Aim for
the daily load curve, weekday vs weekend, monthly/seasonal trend, and the sub-meter
breakdown. Do at least a few aggregations *both* in SQL and in pandas so you can speak
to both — interviewers often ask "would you do this in SQL or Python?"

### Phase 4 — Business analysis & impact
**Goal:** convert patterns into money and recommendations.
**Skills:** scenario modeling, translating analysis into decisions.
**Produce:** `03_business_analysis.ipynb`. Apply a simple time-of-use tariff (e.g.
peak vs off-peak rates), compute the household's annual bill, then model a "what-if":
if X% of shiftable load (water heater / laundry) moved off-peak, what is saved?
Quantify it. End with 3 concrete recommendations.

### Phase 5 — Recurring Excel report
**Goal:** the "recurring report for leadership" deliverable.
**Skills:** Excel pivot tables, charts, clean formatting.
**Produce:** `monthly_energy_report.xlsx` — pick one month, build a one-page report:
KPIs (total kWh, peak day, average daily cost), a pivot table by day, a load-curve
chart. Structure it so that swapping the source data regenerates it. Document the
"refresh steps" so it is genuinely *recurring*, not one-off.

### Phase 6 — Interactive dashboard
**Goal:** the "performance dashboard" deliverable.
**Skills:** building a usable, filterable view.
**Produce:** `dashboard.py` — a Streamlit app with a date-range filter and 3–4 charts
(load curve, sub-meter breakdown, monthly trend, KPI cards). Streamlit is the fastest
path from pandas to a real interface; it screenshots well for the README.

### Phase 7 — Write-up & polish
**Goal:** make it readable and hireable.
**Produce:** `findings_summary.md` (one page, no jargon — written as if for a manager)
and a strong `README.md` with the business questions, your approach, key findings,
screenshots, and how to run it. This is the part most students skip and the part
hiring managers actually read.

---

## 6. How to talk about it in the interview

Prepare a 90-second story following the job description's "start to finish" cue:
*"I worked with ~2 million rows of household smart-meter data. I loaded it into SQL,
then in Python I found the meter had missing intervals and a measurable gap between
total and sub-metered power — I documented that as a data-quality log and decided how
to handle it. Once the data was trustworthy, I found that peak consumption clustered
in [pattern], driven mostly by [circuit]. I modeled a time-of-use tariff and showed
that shifting shiftable load off-peak would save about [X]%. I packaged it as a
monthly Excel report and a Streamlit dashboard so a non-technical team could use it."*

That single paragraph hits SQL, Python, Excel, cleaning, validation, trend-finding,
business impact, dashboards, and stakeholder communication — the entire job posting.

---

## 7. A realistic schedule

Treat each phase as one focused sitting. Phases 2 and 3 are the meatiest; Phase 0 and
Phase 7 are short but do not skip them. Spread over ~2 weeks at a student pace, or a
long week if focused. Commit to Git after every phase — your commit history itself
becomes evidence of how you work.

---

*Next: step-by-step guidance for Phase 0 and Phase 1, with explanations of the
reasoning behind each step.*
