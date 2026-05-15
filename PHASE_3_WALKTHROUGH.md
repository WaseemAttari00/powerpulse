# Phase 3 — Beginner Walkthrough: Exploratory Analysis & Trend-Finding

Now that the data is trustworthy, you find the real patterns in it. This phase answers
business questions 1 and 2: **when** does the household use the most power, and **what**
is driving it.

A key habit this phase builds: you'll do several aggregations in **both SQL and pandas**.
Not busywork — interviewers genuinely ask "would you do this in SQL or in Python?", and
having done both lets you answer from experience.

Same rules: venv active (`venv\Scripts\activate`), run code one block at a time, don't
move on until each **Check** passes.

By the end you'll have `notebooks/02_exploratory_analysis.ipynb`, a
`sql/03_analysis_queries.sql` file, and saved chart images for your README.

---

## Step 3.1 — Set up the notebook and a figures folder

1. In VS Code: File → New File → save as `notebooks/02_exploratory_analysis.ipynb`.
   Select the same `venv` kernel as before when prompted.
2. In your terminal, make a folder to save chart images into:
   ```
   mkdir reports\figures
   ```
3. First cell — make it **Markdown** with a title and what this notebook does:
   ```markdown
   # Phase 3 — Exploratory Analysis: When and Why This Household Uses Power

   Answers business questions 1 (when is consumption highest?) and
   2 (which circuits drive it?). Aggregations are done in both SQL and pandas.
   ```

## Step 3.2 — Load the cleaned data

You have the cleaned data in two places from Phase 2: a parquet file and a SQL table.
You'll use **both** — parquet for pandas work, the SQL table for SQL work. New **code** cell:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# pandas copy (timestamp is the index)
df = pd.read_parquet("../data/processed/power_readings_clean.parquet")

# database connection for running SQL
engine = create_engine("sqlite:///../powerpulse.db")

print(df.shape)
df.head()
```

**Check:** `df.shape` shows ~2 million rows and you see the cleaned columns, including
`total_wh`, `submeter_sum_wh`, and `unmetered_wh` from Phase 2.

> Path reminder: the `../` means "one folder up", because the notebook runs from inside
> `notebooks/`. If a path fails, that's almost always why.

## Step 3.3 — Understand the SQL you're about to write

You haven't used SQL before, so here's the whole idea in three sentences. A SQL query
asks a database a question. **`SELECT`** picks which columns/values you want,
**`GROUP BY`** collapses many rows into one row per group (e.g. one row per hour), and
**aggregate functions** like `AVG()`, `SUM()`, `COUNT()` summarize each group. So
"average power for each hour of the day" is: select the hour and `AVG(power)`, grouped
by hour.

SQLite (your database) extracts time parts with `strftime`:
`strftime('%H', reading_ts)` → hour `'00'`–`'23'`, `strftime('%w', ...)` → weekday
`'0'`(Sun)–`'6'`(Sat), `strftime('%Y-%m', ...)` → month like `'2007-03'`.

## Step 3.4 — Create the SQL analysis file

Create `sql/03_analysis_queries.sql` and paste all four queries below into it. Keeping
your queries in a `.sql` file (not just buried in the notebook) is good practice —
it's a deliverable a reviewer can open and read on its own.

```sql
-- 03_analysis_queries.sql
-- Exploratory aggregations on the cleaned household power data.

-- Q1: Daily load curve - average power for each hour of the day
SELECT strftime('%H', reading_ts) AS hour_of_day,
       ROUND(AVG(global_active_power), 3) AS avg_active_kw
FROM power_readings_clean
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Q2: Weekday vs weekend - average power
SELECT CASE WHEN strftime('%w', reading_ts) IN ('0','6')
            THEN 'weekend' ELSE 'weekday' END AS day_type,
       ROUND(AVG(global_active_power), 3) AS avg_active_kw
FROM power_readings_clean
GROUP BY day_type;

-- Q3: Monthly energy total (kWh) - the seasonal trend
SELECT strftime('%Y-%m', reading_ts) AS month,
       ROUND(SUM(total_wh) / 1000.0, 1) AS total_kwh
FROM power_readings_clean
GROUP BY month
ORDER BY month;

-- Q4: Sub-meter breakdown - total kWh per circuit over the whole period
SELECT ROUND(SUM(sub_metering_1) / 1000.0, 1) AS kitchen_kwh,
       ROUND(SUM(sub_metering_2) / 1000.0, 1) AS laundry_kwh,
       ROUND(SUM(sub_metering_3) / 1000.0, 1) AS water_heater_ac_kwh,
       ROUND(SUM(unmetered_wh)  / 1000.0, 1) AS unmetered_kwh
FROM power_readings_clean;
```

## Step 3.5 — The daily load curve (SQL)

Run the first query from inside the notebook. New **code** cell:

```python
load_curve = pd.read_sql("""
    SELECT strftime('%H', reading_ts) AS hour_of_day,
           ROUND(AVG(global_active_power), 3) AS avg_active_kw
    FROM power_readings_clean
    GROUP BY hour_of_day
    ORDER BY hour_of_day
""", engine)
load_curve
```

```python
ax = load_curve.plot(x="hour_of_day", y="avg_active_kw", kind="bar",
                     figsize=(11, 4), legend=False)
ax.set_title("Average household power by hour of day")
ax.set_xlabel("Hour of day")
ax.set_ylabel("Average active power (kW)")
plt.tight_layout()
plt.savefig("../reports/figures/load_curve_by_hour.png", dpi=120)
plt.show()
```

**Check:** you get a 24-bar chart and a saved PNG in `reports/figures/`. You'll see
consumption is low overnight, rises in the morning, and peaks in the **evening**
(roughly 6–9pm). Write that in a Markdown cell — it's finding #1, and it sets up the
"shift load off-peak" recommendation in Phase 4.

## Step 3.6 — The same thing in pandas (and why)

Now do the identical aggregation without SQL, straight on the DataFrame:

```python
load_curve_pd = df.groupby(df.index.hour)["global_active_power"].mean()
load_curve_pd
```

**Check:** the numbers match the SQL version (tiny rounding aside).

In a Markdown cell, write the comparison in your own words. The gist to capture:
**SQL** is best when the data lives in a database, the dataset is large, or you want a
reusable query others can run; **pandas** is best for fast interactive exploration and
when the data is already in memory and you're about to chart or model it. They're not
rivals — analysts move between them constantly. Being able to say that *from having
done both* is the point of this step.

## Step 3.7 — Weekday vs weekend

```python
day_type = pd.read_sql("""
    SELECT CASE WHEN strftime('%w', reading_ts) IN ('0','6')
                THEN 'weekend' ELSE 'weekday' END AS day_type,
           ROUND(AVG(global_active_power), 3) AS avg_active_kw
    FROM power_readings_clean
    GROUP BY day_type
""", engine)
day_type
```

**Check:** two rows. Typically weekend average is higher (people are home more). State
the finding and the size of the difference.

For a richer view, combine hour *and* day type in pandas — this is easy in pandas and
fiddlier in SQL, which is itself a good illustration of Step 3.6's point:

```python
df["day_type"] = np.where(df.index.dayofweek >= 5, "weekend", "weekday")
pivot = df.pivot_table(values="global_active_power",
                       index=df.index.hour, columns="day_type", aggfunc="mean")
ax = pivot.plot(figsize=(11, 4))
ax.set_title("Load curve: weekday vs weekend")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Average active power (kW)")
plt.tight_layout()
plt.savefig("../reports/figures/load_curve_weekday_weekend.png", dpi=120)
plt.show()
```

**Check:** two lines on one chart. Note where they diverge most (often the weekend
morning fills in, since nobody's left for work).

## Step 3.8 — Monthly / seasonal trend

```python
monthly = pd.read_sql("""
    SELECT strftime('%Y-%m', reading_ts) AS month,
           ROUND(SUM(total_wh) / 1000.0, 1) AS total_kwh
    FROM power_readings_clean
    GROUP BY month ORDER BY month
""", engine)

ax = monthly.plot(x="month", y="total_kwh", figsize=(13, 4), legend=False, marker="o")
ax.set_title("Total household energy per month (kWh)")
ax.set_xlabel("Month"); ax.set_ylabel("Energy (kWh)")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig("../reports/figures/monthly_energy_trend.png", dpi=120)
plt.show()
```

**Check:** a line that rises and falls across the years. Expect **winter peaks** (this
is a French household — heating/water-heating load). One caveat to mention in your
write-up: the months with long data gaps from Phase 2 will look artificially low —
that's the Phase 2 work showing up here, and noting it proves the phases connect.

## Step 3.9 — Sub-meter breakdown (what's driving consumption)

```python
breakdown = pd.read_sql("""
    SELECT ROUND(SUM(sub_metering_1) / 1000.0, 1) AS kitchen_kwh,
           ROUND(SUM(sub_metering_2) / 1000.0, 1) AS laundry_kwh,
           ROUND(SUM(sub_metering_3) / 1000.0, 1) AS water_heater_ac_kwh,
           ROUND(SUM(unmetered_wh)  / 1000.0, 1) AS unmetered_kwh
    FROM power_readings_clean
""", engine)
breakdown
```

```python
shares = breakdown.T.rename(columns={0: "kwh"})
shares["pct"] = (shares["kwh"] / shares["kwh"].sum() * 100).round(1)
ax = shares["kwh"].plot(kind="pie", autopct="%1.1f%%", figsize=(6, 6),
                        ylabel="", title="Energy by circuit (whole period)")
plt.tight_layout()
plt.savefig("../reports/figures/energy_by_circuit.png", dpi=120)
plt.show()
shares
```

**Check:** four slices. Usually the **unmetered** load is the biggest single slice (all
the lighting/outlets not on a sub-meter), with the **water-heater/AC** circuit the
largest *measured* one. That's finding #2, and it tells you which circuit is worth
targeting in Phase 4. Write it down.

## Step 3.10 — Write the findings summary in the notebook

End the notebook with a Markdown cell titled **"Key Findings"** — three or four plain
sentences, e.g.:
- Consumption peaks in the evening (~6–9pm); overnight is lowest.
- Weekends run higher than weekdays, mostly from a fuller weekend morning.
- Energy is seasonal, peaking in winter.
- The water-heater/AC circuit is the largest measured load; most consumption is
  unmetered household load.

This cell is what a busy reviewer reads first. Make it clear and jargon-free — that's
the "communicate with non-technical stakeholders" bullet from the job posting.

## Step 3.11 — Commit Phase 3

```
git add .
git commit -m "Phase 3: exploratory analysis - load curves, weekday/weekend, seasonal trend, sub-meter breakdown"
```

---

## What you've demonstrated

You turned a validated dataset into actual insight: daily and weekly load patterns,
seasonality, and a circuit-level breakdown of what drives consumption — each one tied
back to a business question. You did the core aggregations in **both SQL and pandas**
and can explain when each is the right tool. And you saved clean chart images that
will carry your README.

Your interview line: *"Once the data was trustworthy, I profiled it — the household
peaks in the evening and in winter, weekends run higher than weekdays, and the
water-heater circuit is the biggest measured load. I ran the aggregations in SQL for
reproducibility and in pandas for exploration, so I'm comfortable in both."*

When Phase 3 is committed, come back for Phase 4: turning these patterns into money —
applying a time-of-use tariff and modeling how much shifting load off-peak would save.
