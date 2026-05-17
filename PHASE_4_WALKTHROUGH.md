# Phase 4 — Beginner Walkthrough: Business Analysis & Impact

This is where analysis becomes **money**. You'll take the patterns from Phase 3, apply
a realistic time-of-use tariff, compute what the household actually pays, then model
how much they'd save by shifting load off-peak. The deliverable ends with three plain
recommendations.

This phase is what makes a candidate stand out — most students stop at "here's a
chart." This one says "here's a decision and what it's worth."

Same rules: venv active (`venv\Scripts\activate`), one block at a time,
**Check** before moving on.

By the end you'll have `notebooks/03_business_analysis.ipynb`, two new chart images,
and three concrete recommendations.

---

## Step 4.1 — Set up the notebook

1. VS Code: File → New File → save as `notebooks/03_business_analysis.ipynb`. Pick the
   `venv` kernel.
2. First cell, **Markdown**:
   ```markdown
   # Phase 4 — Business Analysis: Cost, Tariffs, and Savings

   Answers business question 3: what would time-of-use pricing cost this household,
   and how much could shifting load off-peak save?

   **Approach:** apply a simple peak / off-peak tariff to the cleaned minute-level
   data, compute the annual bill, identify shiftable load (the water heater + AC
   sub-meter), then model a what-if scenario where some of that load moves off-peak.
   ```

## Step 4.2 — Load the data and convert to kWh

You need everything in the same unit — kilowatt-hours per minute — so you can
multiply by a price (€ per kWh) cleanly.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_parquet("../data/processed/power_readings_clean.parquet")

# Convert watt-hours to kilowatt-hours per minute.
df["kwh"]           = df["total_wh"]        / 1000.0
df["sub1_kwh"]      = df["sub_metering_1"]  / 1000.0   # kitchen
df["sub2_kwh"]      = df["sub_metering_2"]  / 1000.0   # laundry
df["sub3_kwh"]      = df["sub_metering_3"]  / 1000.0   # water heater + AC
df["unmetered_kwh"] = df["unmetered_wh"]    / 1000.0   # everything else

df[["kwh","sub1_kwh","sub2_kwh","sub3_kwh","unmetered_kwh"]].head()
```

**Check:** values are tiny decimals — that's correct (energy used in a single minute
is a small fraction of a kWh).

## Step 4.3 — Define the tariff

A **time-of-use (TOU) tariff** charges different rates at different hours of the day
— more during high-demand hours, less overnight. Utilities use it to nudge customers
to shift consumption to when the grid has spare capacity. France's "Heures Creuses"
("hollow hours") tariff is the real-world example for this dataset.

We'll use **illustrative** rates — round numbers that are realistic but not tied to any
specific year. Methodology is what's being graded here, not exact euros.

```python
PEAK_RATE_EUR     = 0.20   # €/kWh during peak hours (06:00-22:00)
OFF_PEAK_RATE_EUR = 0.12   # €/kWh during off-peak (22:00-06:00)
FLAT_RATE_EUR     = 0.18   # €/kWh equivalent flat rate to compare against

# Tag every minute as peak or off-peak based on hour of day.
df["is_peak"] = (df.index.hour >= 6) & (df.index.hour < 22)

df["is_peak"].value_counts(normalize=True).round(3)
```

**Check:** roughly two-thirds of minutes are peak (16/24 = 0.667). Add a Markdown
cell stating the tariff assumptions in plain language — this is the kind of
"assumptions" callout reviewers look for.

## Step 4.4 — Compute the annual bill (flat vs TOU)

The dataset spans Dec 2006 to Nov 2010 — so **2007, 2008, 2009 are complete years**.
You'll use those three to compute average annual bills.

Split each minute's energy into a peak bucket and an off-peak bucket, then sum by year:

```python
df["peak_kwh"]    = np.where(df["is_peak"],  df["kwh"], 0)
df["offpeak_kwh"] = np.where(~df["is_peak"], df["kwh"], 0)

annual = df[["kwh","peak_kwh","offpeak_kwh"]].resample("YE").sum()
annual["flat_bill_eur"] = annual["kwh"]        * FLAT_RATE_EUR
annual["tou_bill_eur"]  = (annual["peak_kwh"]    * PEAK_RATE_EUR
                           + annual["offpeak_kwh"] * OFF_PEAK_RATE_EUR)
annual["tou_vs_flat_eur"] = annual["tou_bill_eur"] - annual["flat_bill_eur"]
annual.round(1)
```

**Check:** you'll see annual consumption around **5,000–7,000 kWh** per year and bills
around **€900–€1,300**. The TOU bill should be **higher** than the flat bill — because
this household uses most of its energy during peak hours (the evening peak you found
in Phase 3). That gap *is* the opportunity. Write that observation in a Markdown cell.

## Step 4.5 — Visualize the flat vs TOU comparison

```python
full_years = annual.loc["2007":"2009"]
ax = full_years[["flat_bill_eur","tou_bill_eur"]].plot(
        kind="bar", figsize=(8,4),
        title="Annual electricity bill: flat rate vs time-of-use")
ax.set_xticklabels([d.year for d in full_years.index], rotation=0)
ax.set_ylabel("Annual bill (€)")
plt.tight_layout()
plt.savefig("../reports/figures/bill_flat_vs_tou.png", dpi=120)
plt.show()
```

**Check:** three pairs of bars. TOU bars are taller than flat bars in every year.

## Step 4.6 — Identify the shiftable load

Not every kWh can move. You can't time-shift dinner. But you *can* time-shift loads
that don't care when they run: a water heater on a timer, dishwasher delay-start,
laundry overnight. From Phase 3 you already know **sub-meter 3 (water heater + AC) is
the largest measured circuit**. That's your shift target.

Pick one representative year (2008) and ask: **how much of sub-meter 3's energy is
currently being consumed during peak hours?**

```python
year = "2008"
sub3_total_kwh = df.loc[year, "sub3_kwh"].sum()
sub3_peak_kwh  = df.loc[year, "sub3_kwh"][df.loc[year, "is_peak"]].sum()
sub3_peak_pct  = sub3_peak_kwh / sub3_total_kwh * 100

print(f"{year}: sub-meter 3 total = {sub3_total_kwh:.0f} kWh, "
      f"of which {sub3_peak_kwh:.0f} kWh ({sub3_peak_pct:.1f}%) is in peak hours.")
```

**Check:** you should see that a substantial chunk of sub-meter 3's energy is in peak
hours — every peak kWh you can move saves you the **rate difference** (€0.08/kWh in
our tariff), every year.

## Step 4.7 — The what-if scenario

This is the headline number of the project: *"if you shift X% of the water-heater load
off-peak, you save €Y per year."*

```python
RATE_DIFF = PEAK_RATE_EUR - OFF_PEAK_RATE_EUR   # €0.08/kWh

scenarios = pd.DataFrame({
    "shift_pct": [0, 10, 25, 50, 75, 100],
})
scenarios["annual_kwh_shifted"] = scenarios["shift_pct"] / 100 * sub3_peak_kwh
scenarios["annual_savings_eur"] = scenarios["annual_kwh_shifted"] * RATE_DIFF
scenarios.round(1)
```

**Check:** the table reads like a menu — "shift 50% → save €X". That's the kind of
output a non-technical stakeholder can immediately use.

Plot the sensitivity:

```python
ax = scenarios.plot(x="shift_pct", y="annual_savings_eur",
                    marker="o", figsize=(8,4), legend=False)
ax.set_title("Annual savings vs % of water-heater peak load shifted off-peak")
ax.set_xlabel("% of sub-meter 3 peak load shifted to off-peak hours")
ax.set_ylabel("Annual savings (€)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../reports/figures/savings_sensitivity.png", dpi=120)
plt.show()
```

**Check:** a clean line going up and to the right — the kind of chart a manager
actually understands at a glance.

## Step 4.8 — Stress-test the numbers (a small but important step)

Repeat the calculation for the other complete years (2007, 2009) to confirm the
finding isn't a fluke of one year. This is what "data validation" looks like applied
to *conclusions*, not just inputs.

```python
for y in ["2007", "2008", "2009"]:
    peak_kwh = df.loc[y, "sub3_kwh"][df.loc[y, "is_peak"]].sum()
    savings_at_50 = 0.50 * peak_kwh * RATE_DIFF
    print(f"{y}: shifting 50% of sub-meter 3 peak load saves €{savings_at_50:.2f}")
```

**Check:** all three years should give a savings figure of broadly similar magnitude.
If they do, your conclusion is robust. Write that in a Markdown cell — *"checked
across three full years, the savings are consistent."*

## Step 4.9 — Write the three recommendations

End the notebook with a Markdown cell titled **"Recommendations"**. Phrase each one
as: action → impact → confidence. Example:

> 1. **Put the water heater on an off-peak timer.** Shifting 50% of the water-heater
>    + AC circuit's peak-hour energy to off-peak hours saves roughly **€X per year**
>    at our tariff assumptions. This is the single biggest lever, validated across
>    three full years of data.
> 2. **Schedule laundry and dishwasher cycles overnight.** Sub-meter 2 has smaller
>    but real shiftable load; combined with the timer, this stretches savings further
>    without any change to lifestyle.
> 3. **Switch to a time-of-use tariff *only after* shifting load.** Under current
>    usage, TOU is more expensive than a flat rate (the evening peak dominates). The
>    tariff becomes the cheaper option once the shifts above are made — sequencing
>    matters.

That third recommendation is the kind of "I actually thought about this" insight that
sets a strong candidate apart from a competent one.

## Step 4.10 — Commit Phase 4

```
git add .
git commit -m "Phase 4: business analysis - TOU vs flat bill, shiftable-load model, savings sensitivity, recommendations"
```

---

## What you've demonstrated

You took validated, profiled data and answered a real business question with a
**number**, then validated that number across multiple years, then translated it into
three concrete actions a non-technical person can act on. That arc — pattern →
quantification → recommendation — is what every "business impact" bullet on a data
analyst job description is really asking for.

Your interview line: *"I built a time-of-use tariff model on top of the cleaned data
and showed that the household's evening peak makes TOU more expensive than a flat
rate today — but if they put the water heater on an off-peak timer (the largest
measured circuit), they save about €X per year, a result I cross-checked across three
full years. So the recommendation isn't just 'switch tariffs' — it's 'shift load
first, then switch.'"*

When Phase 4 is committed, come back for Phase 5: building the recurring monthly
Excel report — the "report for leadership" deliverable.
