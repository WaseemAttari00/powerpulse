# Phase 6 — Beginner Walkthrough: The Interactive Streamlit Dashboard

This phase delivers the "performance dashboard" bullet from the job posting — and
arguably the highest-impact thing in the whole repo for *visual* impression. A reviewer
who opens your GitHub README and sees a screenshot of a clean interactive dashboard is
sold before they've read a line of code.

You'll build it with **Streamlit** — a Python framework where every line of code
becomes a piece of a web app. No HTML, no JavaScript, no front-end knowledge needed.
You write `st.line_chart(df)` and a line chart appears in the browser.

Same rules: venv active (`venv\Scripts\activate`), one step at a time,
**Check** before moving on.

By the end you'll have `app/dashboard.py`, a running dashboard at
`http://localhost:8501`, and at least one screenshot saved to `reports/figures/` for
the README.

---

## Step 6.1 — How Streamlit works (60 seconds)

Streamlit is a Python library that runs your script top-to-bottom and turns each
`st.something(...)` call into a piece of the page. When a user changes a filter (a
date picker, a slider), Streamlit **re-runs the whole script** with the new value —
which sounds wasteful but is what makes it trivially simple to write. You write plain
linear Python; Streamlit handles the "reactivity" automatically.

You launch it with `streamlit run app/dashboard.py` and it opens in your browser.

The one performance trick: wrap your expensive data load in `@st.cache_data` so the
parquet file is only read once, not on every re-run.

## Step 6.2 — Create the dashboard file

In VS Code: File → New File → save as `app/dashboard.py`. (`app/` was created back in
Phase 0.) Start with imports and page config — this should be the **first** Streamlit
call in the file:

```python
"""
PowerPulse — Interactive Energy Dashboard

Run from the project root:
    streamlit run app/dashboard.py
Then open http://localhost:8501 in your browser.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="PowerPulse — Energy Dashboard",
    page_icon=None,
    layout="wide",            # use the full width of the browser
)

DATA_PATH = Path("data/processed/power_readings_clean.parquet")
```

`layout="wide"` matters — the default is a narrow centered column that makes
dashboards feel cramped.

## Step 6.3 — Cached data loading

```python
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load cleaned data once and cache it. Re-runs of the script reuse this."""
    df = pd.read_parquet(DATA_PATH)
    df["kwh"]      = df["total_wh"] / 1000.0
    df["sub1_kwh"] = df["sub_metering_1"] / 1000.0
    df["sub2_kwh"] = df["sub_metering_2"] / 1000.0
    df["sub3_kwh"] = df["sub_metering_3"] / 1000.0
    df["unmetered_kwh"] = df["unmetered_wh"] / 1000.0
    return df

df = load_data()
```

**What `@st.cache_data` does:** the first time the page loads, this function reads
2M rows from disk (a few seconds). Every subsequent re-run — every time a user moves
a filter — Streamlit reuses the cached result. Without this decorator, the dashboard
would feel sluggish for no reason.

## Step 6.4 — Sidebar: filters

The sidebar is where filters live. Streamlit creates it automatically when you call
`st.sidebar.something(...)`:

```python
st.sidebar.header("Filters")

min_date = df.index.min().date()
max_date = df.index.max().date()
default_start = pd.Timestamp("2008-01-01").date()
default_end   = pd.Timestamp("2008-12-31").date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(default_start, default_end),
    min_value=min_date,
    max_value=max_date,
)

# st.date_input returns a tuple when the user has picked both ends
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = default_start, default_end

st.sidebar.markdown("---")
st.sidebar.header("Tariff (€/kWh)")
peak_rate     = st.sidebar.number_input("Peak rate",     value=0.20, step=0.01, format="%.2f")
off_peak_rate = st.sidebar.number_input("Off-peak rate", value=0.12, step=0.01, format="%.2f")
peak_start    = st.sidebar.slider("Peak hours start", 0, 23, 6)
peak_end      = st.sidebar.slider("Peak hours end",   0, 23, 22)

# Apply the date filter
mask = (df.index.date >= start) & (df.index.date <= end)
view = df.loc[mask].copy()
view["is_peak"] = (view.index.hour >= peak_start) & (view.index.hour < peak_end)
```

**Why expose tariff and peak hours in the sidebar:** these aren't decorative — they
let a stakeholder explore "what if peak hours were 5-10pm instead?" without changing
code. That interactivity is the whole reason a dashboard exists. Make this point in
your README.

## Step 6.5 — Title and KPI cards row

```python
st.title("PowerPulse — Household Energy Dashboard")
st.caption(f"Showing data from **{start}** to **{end}** "
           f"({len(view):,} minute-level readings).")

# Pre-compute the numbers used by the KPI cards
total_kwh        = view["kwh"].sum()
peak_kwh         = view.loc[view["is_peak"], "kwh"].sum()
offpeak_kwh      = view.loc[~view["is_peak"], "kwh"].sum()
total_cost       = peak_kwh * peak_rate + offpeak_kwh * off_peak_rate
daily            = view["kwh"].resample("D").sum()
peak_day_kwh     = daily.max()
peak_day_label   = daily.idxmax().strftime("%Y-%m-%d") if not daily.empty else "—"
peak_share_pct   = (peak_kwh / total_kwh * 100) if total_kwh else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total energy",      f"{total_kwh:,.0f} kWh")
c2.metric("Estimated cost",    f"€ {total_cost:,.0f}")
c3.metric("Peak day",          peak_day_label, f"{peak_day_kwh:,.1f} kWh")
c4.metric("Peak-hour share",   f"{peak_share_pct:,.0f}%")

st.markdown("---")
```

`st.columns(4)` puts the four KPI cards side-by-side. `st.metric` is Streamlit's
purpose-built "big number with a small label" card — designed exactly for this.

**Check (mentally for now, you'll verify in Step 6.10):** the KPI row should be the
first thing a viewer sees. KPIs above the fold, charts below — that ordering is what
"executive view" means.

## Step 6.6 — Chart 1: daily energy trend

```python
st.subheader("Daily energy use")
st.line_chart(daily, height=260, y_label="kWh")
```

Two lines of code, one full chart. Streamlit's built-in charts are deliberately
simple — for line, bar, and area charts they're perfect.

## Step 6.7 — Chart 2: hourly load curve (matplotlib)

For shapes that need more control (titles, axis labels, custom styling), drop down to
matplotlib and hand the figure to `st.pyplot`:

```python
st.subheader("Average power by hour of day")

hourly = view.groupby(view.index.hour)["global_active_power"].mean()

fig, ax = plt.subplots(figsize=(10, 3))
ax.bar(hourly.index, hourly.values, color="#305496")
ax.axvspan(peak_start, peak_end, alpha=0.10, color="orange",
           label="peak hours")
ax.set_xlabel("Hour of day")
ax.set_ylabel("Average active power (kW)")
ax.set_xticks(range(0, 24))
ax.legend(loc="upper left")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)
```

The orange shaded band visualises the peak hours the user picked in the sidebar —
move the sliders and the band moves. That kind of small touch is what makes a
dashboard feel responsive instead of static.

**Note the `plt.close(fig)`:** Streamlit re-runs the script often, and without
closing each figure you'll leak memory after enough re-runs. Small habit, worth
having.

## Step 6.8 — Chart 3: sub-meter breakdown

```python
st.subheader("What's driving consumption")

breakdown = pd.Series({
    "Kitchen (sub-meter 1)":            view["sub1_kwh"].sum(),
    "Laundry (sub-meter 2)":            view["sub2_kwh"].sum(),
    "Water heater + AC (sub-meter 3)":  view["sub3_kwh"].sum(),
    "Unmetered (everything else)":      view["unmetered_kwh"].sum(),
}).sort_values(ascending=True)

col_left, col_right = st.columns([2, 1])
with col_left:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.barh(breakdown.index, breakdown.values, color="#305496")
    ax.set_xlabel("Energy used (kWh)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
with col_right:
    pct = (breakdown / breakdown.sum() * 100).round(1)
    st.dataframe(pct.rename("share %").to_frame(),
                 use_container_width=True)
```

**Two design choices to call out:** horizontal bars (easier to read circuit names than
a pie chart with rotated labels), and the share table next to the chart for people
who want exact numbers. Splitting into two `st.columns` puts them side-by-side.

## Step 6.9 — Chart 4: weekday vs weekend

```python
st.subheader("Weekday vs weekend")

view["day_type"] = np.where(view.index.dayofweek >= 5, "weekend", "weekday")
pivot = view.pivot_table(values="global_active_power",
                         index=view.index.hour, columns="day_type", aggfunc="mean")

fig, ax = plt.subplots(figsize=(10, 3))
pivot.plot(ax=ax)
ax.set_xlabel("Hour of day")
ax.set_ylabel("Average active power (kW)")
ax.set_xticks(range(0, 24))
ax.legend(title="")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("---")
st.caption("Source: UCI 'Individual household electric power consumption' dataset. "
           "Cleaning, validation, and aggregation pipeline: see the Phase 2 and 3 "
           "notebooks.")
```

Always end a dashboard with a **source line**. It tells a reviewer the numbers aren't
invented and points them to your validation work — that's the data-accuracy bullet
from the job posting hiding in plain sight.

## Step 6.10 — Run it

In the terminal, from your project root:
```
streamlit run app/dashboard.py
```

**Check:** a browser tab opens at `http://localhost:8501` showing your dashboard. The
first load takes a few seconds (the parquet read); subsequent filter changes feel
near-instant thanks to `@st.cache_data`.

Now actually **use** it for a minute — it's the best way to find what doesn't work yet:
- Move the date range to a single month — KPIs and charts should update.
- Drag the peak-hours sliders — the orange band should move and the cost should change.
- Bump the peak rate — total cost should jump.
- Pick a date range with no data (very early Dec 2006 only) — does anything break?
  This is a quick robustness check.

**Stop the app** when you're done: in the terminal, press **Ctrl+C**.

> If you get an error about Plotly or some unrelated package on startup, ignore it —
> Streamlit prints a few warnings about optional integrations on first launch. The
> dashboard still works.

## Step 6.11 — Take screenshots for the README

The screenshots are what carry your GitHub profile. With the dashboard running:

1. Set a representative date range (e.g. Mar 2008 — 31 days, clear patterns).
2. **Full-page screenshot:** Windows Snipping Tool (`Win + Shift + S`) → rectangular
   capture → save to `reports/figures/dashboard_full.png`. Or, in Chrome, press
   `Ctrl+Shift+I` → `Ctrl+Shift+P` → type "Capture full size screenshot".
3. **Optional second shot:** zoom into just the KPI cards row plus the load curve —
   that's the most photogenic part. Save as `reports/figures/dashboard_kpis.png`.

Add the screenshots to your README later in Phase 7 — but capture them *now* while the
dashboard is fresh in your mind and you remember which filter setup made it look best.

## Step 6.12 — Commit Phase 6

```
git add .
git commit -m "Phase 6: interactive Streamlit dashboard - KPI cards, daily trend, hourly load curve, sub-meter breakdown, weekday/weekend split, date and tariff filters"
```

---

## What you've demonstrated

You built a real interactive web dashboard from your dataset — four charts, four KPI
cards, four interactive filters — in one Python file. Stakeholders can change the
date range and tariff and watch the numbers update. The dashboard is anchored to the
same cleaned, validated data your analysis notebooks use, so the numbers in the
dashboard *are* the numbers in your report. That consistency is the data-integrity
story carried all the way through.

Your interview line: *"I built a Streamlit dashboard on the cleaned data with KPI
cards and four charts. The filters in the sidebar let a stakeholder change the date
range, the tariff rates, and even the definition of peak hours — so it's not just a
viewer, it's a what-if tool. The screenshots are in the README. Behind the scenes
it's cached so it stays fast even on 2 million rows."*

When Phase 6 is committed, come back for Phase 7 — the final polish: a strong README,
a plain-language findings summary, and the screenshots assembled into the front door
of your GitHub repo. That's what hiring managers actually read.
