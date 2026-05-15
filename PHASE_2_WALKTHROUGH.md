# Phase 2 — Beginner Walkthrough: Cleaning & Validation

This is the most important phase for interviews. The goal is not just "clean the data"
— it's to **find what's wrong, decide what to do about it, and document every decision**.
That paper trail is your "data accuracy and quality control" evidence.

Same rules as before: activate your venv first (`venv\Scripts\activate` — prompt shows
`(venv)`), type code one block at a time, and don't move on until each **Check** passes.

By the end you'll have a notebook called `notebooks/01_cleaning_and_validation.ipynb`
and a cleaned dataset saved in `data/processed/`.

---

## Step 2.1 — What a Jupyter notebook is, and how to make one

A **notebook** is a file where you write code in small blocks called **cells** and run
them one at a time, seeing the output (numbers, tables, charts) right underneath each
cell. It's the standard tool for data analysis because it lets you explore step by
step and keeps your code and results together — which doubles as a readable report.

To create one:
1. In VS Code, open your project folder if it isn't open (File → Open Folder → your
   "Data Science Project" folder).
2. File → New File → save it as `notebooks/01_cleaning_and_validation.ipynb`.
   The `.ipynb` extension makes VS Code open it as a notebook.
3. VS Code may ask you to "Select a Kernel" — choose the Python from your `venv`
   folder (it will say something like `venv (Python 3.x)`). The "kernel" is just the
   Python engine that runs your cells.

**How to use cells:**
- Click "+ Code" to add a code cell, "+ Markdown" to add a text cell.
- Press **Shift+Enter** to run the selected cell and move to the next one.
- A `[1]`, `[2]`... number appears to the left of each code cell showing the order it
  ran in.

**Do this now:** make the very first cell a **Markdown** cell and paste your five
business questions and a title into it. A notebook that opens with "here's what I'm
trying to answer" reads like a professional report, not a scratchpad.

```markdown
# Phase 2 — Cleaning & Validation: Household Power Data

**Business questions this project answers:**
1. When does this household use the most power?
2. What is driving consumption (which circuits)?
3. What would time-of-use pricing cost, and what could shifting load save?
4. Can we trust the meter data?
5. What should a recurring monthly energy report contain?

This notebook focuses on Question 4: making the data trustworthy.
```

## Step 2.2 — Load the data from SQL into pandas

In Phase 1 you put the data into a SQLite database. Now pull it back out into pandas
(a "DataFrame" is just a table you can manipulate in Python). New **code** cell:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

engine = create_engine("sqlite:///powerpulse.db")
df = pd.read_sql("SELECT * FROM power_readings", engine)

# Make reading_ts a real datetime and use it as the index (so time operations work).
df["reading_ts"] = pd.to_datetime(df["reading_ts"])
df = df.set_index("reading_ts").sort_index()

print(df.shape)
df.head()
```

**Check:** `df.shape` prints `(2075259, 7)` — about 2 million rows, 7 columns. `df.head()`
shows a table of the first 5 rows with a timestamp on the left.

> Note on paths: if the notebook can't find `powerpulse.db`, it's because the notebook
> runs from the `notebooks/` folder. Either move `powerpulse.db` next to the notebook,
> or change the line to `create_engine("sqlite:///../powerpulse.db")` — the `../` means
> "look one folder up".

## Step 2.3 — Quantify the missing data

You can't fix what you haven't measured. First, *how much* is missing:

```python
missing = df.isna().sum()
missing_pct = (df.isna().mean() * 100).round(2)
pd.DataFrame({"missing_rows": missing, "missing_pct": missing_pct})
```

**Check:** each power column has roughly **25,979 missing values (~1.25%)**. Notice
they're the same count across columns — a clue that whole rows are missing together,
not scattered individual values.

Now find *where* the missing data is — does it cluster in time?

```python
# Resample to daily counts of missing rows.
daily_missing = df["global_active_power"].isna().resample("D").sum()
daily_missing[daily_missing > 0].sort_values(ascending=False).head(15)
```

```python
daily_missing.plot(figsize=(12, 3), title="Missing readings per day")
plt.ylabel("missing minutes")
plt.show()
```

**Check:** you'll see the gaps aren't random — they come in **chunks** (whole days or
multi-hour stretches where the meter logged nothing). This matters: it means the meter
had outages, and it changes how you should fill them. Write that observation into a
Markdown cell — it's a real finding.

## Step 2.4 — Decide how to handle the missing values (and justify it)

There's no single "correct" answer — what matters is making a *defensible* choice and
writing down *why*. Here's a reasonable, explainable approach for time-series meter data:

- **Short gaps (a few minutes):** interpolate — fill with a straight line between the
  known values on either side. Over a few minutes, power consumption doesn't jump
  wildly, so this is a safe estimate.
- **Long gaps (hours or whole days):** do **not** interpolate — there's no real
  information there, and inventing a day of data would corrupt your monthly totals.
  Leave them missing and simply exclude those periods from totals, noting it.

```python
# Identify gap lengths. A "gap" is a run of consecutive missing minutes.
is_missing = df["global_active_power"].isna()
gap_id = (is_missing != is_missing.shift()).cumsum()
gap_sizes = is_missing.groupby(gap_id).transform("sum").where(is_missing)

SHORT_GAP_MAX = 15  # minutes — our cutoff between "interpolate" and "leave alone"

power_cols = ["global_active_power", "global_reactive_power", "voltage",
              "global_intensity", "sub_metering_1", "sub_metering_2", "sub_metering_3"]

df_clean = df.copy()
short_gap_mask = is_missing & (gap_sizes <= SHORT_GAP_MAX)

for col in power_cols:
    # interpolate everywhere, but only KEEP the interpolated value where it's a short gap
    interpolated = df_clean[col].interpolate(method="time", limit=SHORT_GAP_MAX)
    df_clean[col] = df_clean[col].where(~short_gap_mask, interpolated)

print("Missing before:", df["global_active_power"].isna().sum())
print("Missing after :", df_clean["global_active_power"].isna().sum())
```

**Check:** "Missing after" is smaller than "Missing before" but **not zero** — the long
gaps are intentionally still missing. That's correct. In a Markdown cell, record the
rule and the reason exactly as above. This is the kind of decision an interviewer will
ask you to defend, so write it in your own words.

## Step 2.5 — Physical plausibility checks

Missing data is the obvious problem. The subtler one: values that are *present but
impossible*. As an ECE student you actually know the physics here — use it.

```python
checks = {
    "voltage outside 200-260 V": ((df_clean["voltage"] < 200) | (df_clean["voltage"] > 260)),
    "negative active power":     (df_clean["global_active_power"] < 0),
    "negative sub-metering":     ((df_clean[["sub_metering_1","sub_metering_2","sub_metering_3"]] < 0).any(axis=1)),
}
for label, mask in checks.items():
    print(f"{label}: {mask.sum()} rows")
```

**Check:** for this dataset these should mostly come back **0** — which is itself a
result worth stating: "I tested for physically impossible values (out-of-range voltage,
negative power) and found none, which raised my confidence in the meter." Knowing what
*didn't* go wrong is part of validation. (If any column does flag rows, investigate
and decide — drop or cap — and log it.)

## Step 2.6 — The reconciliation check (the centerpiece)

This is the single most interview-worthy thing in the project. The dataset has a total
(`global_active_power`) and three sub-meters that each measure part of the house. They
should be *consistent* with each other. Checking that consistency is exactly what
"catching a reporting issue" means.

The physics: `global_active_power` is in **kilowatts**, averaged over each minute. The
energy used in that one minute, in **watt-hours**, is `global_active_power * 1000 / 60`.
The three sub-meters are already in watt-hours. So:

> **unmetered remainder** = total energy this minute − (sub_meter_1 + 2 + 3)

That remainder is the energy used by everything *not* on the three sub-meters (lights,
outlets, etc.). It should almost always be **≥ 0** — the parts can't exceed the whole.

```python
df_clean["total_wh"] = df_clean["global_active_power"] * 1000 / 60
df_clean["submeter_sum_wh"] = (df_clean["sub_metering_1"]
                               + df_clean["sub_metering_2"]
                               + df_clean["sub_metering_3"])
df_clean["unmetered_wh"] = df_clean["total_wh"] - df_clean["submeter_sum_wh"]

negative = df_clean["unmetered_wh"] < 0
print(f"Rows where parts exceed the whole: {negative.sum()} "
      f"({negative.mean()*100:.3f}%)")
print(df_clean["unmetered_wh"].describe())
```

```python
# What share of consumption do the three sub-meters actually capture?
covered = df_clean["submeter_sum_wh"].sum() / df_clean["total_wh"].sum() * 100
print(f"Sub-meters capture {covered:.1f}% of total energy; "
      f"{100-covered:.1f}% is unmetered.")
```

**Check & what to write up:** you'll find the unmetered remainder is **positive almost
all the time** (good — the data is internally consistent), but there may be a *small*
number of slightly-negative rows from rounding/measurement noise. Both outcomes are
findings:
- "The sub-metering reconciles with the total — the three meters account for ~X% of
  consumption, the rest is unmetered household load."
- "A tiny fraction of rows showed the sub-meters slightly exceeding the total, which I
  attribute to rounding in the minute-averaging; I flagged them rather than discarding,
  since the effect is negligible."

Either way, you *checked*, you *quantified*, and you *explained*. That's the whole job.

## Step 2.7 — Build the data quality log

Now collect every decision into one table. This is the artifact you'll point to in an
interview. New **code** cell:

```python
quality_log = pd.DataFrame([
    {"issue": "Missing meter readings",
     "finding": "~25,979 rows (~1.25%), clustered in multi-hour/day outages",
     "decision": "Interpolate gaps <=15 min; leave longer gaps missing",
     "rationale": "Short gaps are safe to estimate; long gaps have no real signal"},
    {"issue": "Out-of-range voltage / negative power",
     "finding": "0 rows found",
     "decision": "No action needed",
     "rationale": "Tested for impossible values; meter data passed"},
    {"issue": "Sub-metering vs total reconciliation",
     "finding": "Unmetered remainder positive in ~99.9%+ of rows",
     "decision": "Flag the rare negative rows, do not drop",
     "rationale": "Negatives are negligible rounding noise from minute-averaging"},
])
quality_log
```

Put a Markdown cell above it titled **"Data Quality Log"** with one sentence: *"Every
data issue found during validation, the decision made, and why."*

## Step 2.8 — Save the cleaned dataset

Save the cleaned data so later phases don't repeat this work. Parquet is a compact,
fast file format for tables.

```python
df_clean.to_parquet("../data/processed/power_readings_clean.parquet")

# Also write it back to the database as a separate clean table.
df_clean.reset_index().to_sql("power_readings_clean", engine,
                              if_exists="replace", index=False)
print("Saved cleaned data to parquet and to the 'power_readings_clean' SQL table.")
```

**Check:** a file appears at `data/processed/power_readings_clean.parquet`, and your
database now has a second table `power_readings_clean`.

## Step 2.9 — Commit Phase 2

Back in the terminal:
```
git add .
git commit -m "Phase 2: cleaning and validation - missing-data handling, plausibility checks, sub-metering reconciliation, data quality log"
```

---

## What you've demonstrated

You took raw meter data and made it trustworthy: you **measured** the missing data and
showed it clustered in outages, made a **defensible, documented** choice about filling
it, tested for **physically impossible** values, and ran a genuine **reconciliation
check** between the total and the sub-meters — then logged every decision in one place.

Your interview line for this phase: *"Before analyzing anything, I validated the data.
I found the meter had outage gaps and I handled short and long gaps differently for a
reason I can defend. Then I reconciled the household total against the three sub-meters
to confirm the data was internally consistent, and I kept a data-quality log of every
issue and decision."* That sentence alone answers two of the job posting's six bullets.

When your cleaned table is saved and committed, come back for Phase 3: exploratory
analysis and trend-finding — where you start actually answering business questions 1
and 2.
