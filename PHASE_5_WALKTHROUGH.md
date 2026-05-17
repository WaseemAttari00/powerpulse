# Phase 5 — Beginner Walkthrough: The Recurring Monthly Excel Report

This phase delivers the "recurring reports / performance dashboards for leadership"
bullet from the job posting. You'll build a **Python script** that produces a polished
multi-sheet Excel report for any month — and re-running the script with a different
month regenerates the report. That word *recurring* is what separates a real
deliverable from a one-off chart.

Two non-obvious design choices you'll make in this phase, and should be ready to
explain in an interview:

1. **Excel formulas, not hardcoded numbers.** Totals, costs, and averages are written
   as formulas (`=SUM(...)`) so the workbook stays alive — a stakeholder editing a
   daily figure sees totals update. Hardcoding numbers makes the file dead.
2. **Parameters at the top of a Summary sheet.** Tariff rates live in named cells so
   leadership can change a rate and see the bill update — without touching Python.

Same rules: venv active (`venv\Scripts\activate`), one step at a time,
**Check** before moving on.

By the end you'll have `reports/build_monthly_report.py`, at least two generated
report files in `reports/`, and a short refresh instructions block in your README.

---

## Step 5.1 — Design the report (before writing code)

A one-page monthly report has three things on it. Spend 2 minutes sketching this on
paper — it's faster than coding into a blank file:

1. **Summary tab** — top-of-page KPIs a manager reads in 10 seconds:
   - Reporting month
   - Total kWh
   - Peak day (date + kWh)
   - Average daily kWh
   - Total cost (€) under the tariff
   - Tariff parameters (editable cells)
2. **Daily breakdown tab** — a table: date, total kWh, peak kWh, off-peak kWh, daily
   cost. Totals row at the bottom uses SUM formulas.
3. **Hourly load curve tab** — average power by hour of day, with a line chart.

That's it. Resist the temptation to add a fourth tab — leadership reports earn trust
by being short.

## Step 5.2 — Create the script file

In VS Code: File → New File → save as `reports/build_monthly_report.py`. This is a
plain Python script (not a notebook) — that matters, because a script is what gets
*scheduled* to run every month. You can re-run it from the terminal in one line.

Paste the imports and configuration block first:

```python
"""
PowerPulse — Monthly Energy Report Generator

Usage:
    python reports/build_monthly_report.py 2008-03

If no month is given, defaults to the most recent complete month in the data.
Output: reports/monthly_energy_report_<month>.xlsx
"""
import sys
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, Reference
from openpyxl.utils import get_column_letter

# --- Configuration ---------------------------------------------------------
DATA_PATH      = Path("data/processed/power_readings_clean.parquet")
OUTPUT_DIR     = Path("reports")
PEAK_RATE_EUR     = 0.20   # default peak rate; user can change in the Summary sheet
OFF_PEAK_RATE_EUR = 0.12
PEAK_HOURS = range(6, 22)   # 06:00 inclusive to 22:00 exclusive
HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", start_color="305496")
KPI_LABEL_FONT = Font(name="Calibri", bold=True, size=11)
KPI_VALUE_FONT = Font(name="Calibri", size=11)
```

**Why a script and not a notebook here?** Notebooks are for exploration. Scripts are
for *production*. A monthly report needs to run unattended — being a script means it
can later be triggered by Windows Task Scheduler, a GitHub Action, or just a
double-click. That distinction is exactly the kind of thing interviewers probe.

## Step 5.3 — Load the data and pick the month

Add this to the script:

```python
def load_month(month_str: str | None) -> tuple[str, pd.DataFrame]:
    """Load cleaned data; return (month_str, df_for_that_month)."""
    df = pd.read_parquet(DATA_PATH)

    if month_str is None:
        # Default: the most recent month that has at least 25 days of data
        completeness = df.resample("ME")["global_active_power"].count() / (60 * 24)
        complete_months = completeness[completeness >= 25].index
        if len(complete_months) == 0:
            raise SystemExit("No complete months found in data.")
        month_str = complete_months.max().strftime("%Y-%m")

    month_df = df.loc[month_str].copy()
    if month_df.empty:
        raise SystemExit(f"No data for month {month_str}.")
    return month_str, month_df
```

**What's happening:** if the user runs the script without specifying a month, we pick
"the most recent month with at least 25 days of data". That kind of small intelligent
default is what makes a tool recurring-friendly — it does the right thing if a tired
analyst just hits Enter.

## Step 5.4 — Aggregate the month into a daily table

```python
def daily_table(month_df: pd.DataFrame) -> pd.DataFrame:
    """One row per day with kWh totals and peak/off-peak split."""
    month_df = month_df.copy()
    month_df["kwh"]      = month_df["total_wh"] / 1000.0
    month_df["is_peak"]  = month_df.index.hour.isin(PEAK_HOURS)
    month_df["peak_kwh"]    = month_df["kwh"].where(month_df["is_peak"], 0)
    month_df["offpeak_kwh"] = month_df["kwh"].where(~month_df["is_peak"], 0)

    daily = month_df.resample("D").agg(
        total_kwh=("kwh", "sum"),
        peak_kwh=("peak_kwh", "sum"),
        offpeak_kwh=("offpeak_kwh", "sum"),
    ).round(3)
    daily.index = daily.index.date  # cleaner display in Excel
    return daily
```

**Check (mentally):** the function returns one row per day, three numeric columns. The
peak/off-peak split adds up to `total_kwh`. That property — a sanity check you do in
your head as you design — is the kind of small validation muscle Phase 2 was building.

## Step 5.5 — The Summary sheet (with editable parameters)

Now the interesting part. The Summary sheet has the headline KPIs and — crucially —
two cells where the tariff rates live. Everything that depends on rates references
those cells. Change a rate, the cost updates. That's "dynamic":

```python
def write_summary(ws, month_str, daily, n_days):
    ws.title = "Summary"

    # Title
    ws["A1"] = f"Monthly Energy Report — {month_str}"
    ws["A1"].font = Font(name="Calibri", bold=True, size=16)
    ws.merge_cells("A1:D1")

    # Tariff parameters (editable — these are the cells stakeholders can change)
    ws["A3"] = "Tariff parameters"
    ws["A3"].font = KPI_LABEL_FONT
    ws["A4"] = "Peak rate (€/kWh)"     ; ws["B4"] = PEAK_RATE_EUR
    ws["A5"] = "Off-peak rate (€/kWh)" ; ws["B5"] = OFF_PEAK_RATE_EUR
    for cell in (ws["B4"], ws["B5"]):
        cell.number_format = "0.00"
        cell.fill = PatternFill("solid", start_color="FFF2CC")  # yellow = "editable"

    # KPIs — written as FORMULAS referencing the Daily sheet, so they recalc
    # automatically when the daily table is edited.
    last_row = 1 + n_days + 1   # daily header row + n data rows + 1 totals row
    daily_range_total = f"'Daily breakdown'!B2:B{1+n_days}"
    daily_range_peak  = f"'Daily breakdown'!C2:C{1+n_days}"
    daily_range_offpk = f"'Daily breakdown'!D2:D{1+n_days}"
    daily_range_date  = f"'Daily breakdown'!A2:A{1+n_days}"

    ws["A7"] = "Key metrics" ; ws["A7"].font = KPI_LABEL_FONT
    ws["A8"]  = "Total energy (kWh)"      ; ws["B8"]  = f"=SUM({daily_range_total})"
    ws["A9"]  = "Peak-hour energy (kWh)"  ; ws["B9"]  = f"=SUM({daily_range_peak})"
    ws["A10"] = "Off-peak energy (kWh)"   ; ws["B10"] = f"=SUM({daily_range_offpk})"
    ws["A11"] = "Average daily energy (kWh)" ; ws["B11"] = f"=AVERAGE({daily_range_total})"
    ws["A12"] = "Peak day (kWh)"          ; ws["B12"] = f"=MAX({daily_range_total})"
    ws["A13"] = "Peak day date"           ; ws["B13"] = (
        f"=INDEX({daily_range_date},MATCH(MAX({daily_range_total}),{daily_range_total},0))"
    )
    ws["A14"] = "Total cost (€)"          ; ws["B14"] = (
        f"=SUM({daily_range_peak})*$B$4 + SUM({daily_range_offpk})*$B$5"
    )

    # Formatting
    for r in range(8, 15):
        ws.cell(row=r, column=1).font = KPI_LABEL_FONT
        ws.cell(row=r, column=2).font = KPI_VALUE_FONT
        if r != 13:
            ws.cell(row=r, column=2).number_format = "#,##0.00"
    ws["B14"].number_format = '"€"#,##0.00'

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18
```

**Two things to notice:**
- The yellow-shaded cells (`B4`, `B5`) are the **editable inputs**. Yellow is the
  industry convention for "user-editable cell" — call that out in your interview.
- Every KPI is a formula referencing the Daily sheet, not a hardcoded number. If a
  daily row is corrected, the totals fix themselves.

## Step 5.6 — The Daily breakdown sheet (with formulas)

```python
def write_daily(ws, daily):
    ws.title = "Daily breakdown"
    headers = ["Date", "Total kWh", "Peak kWh", "Off-peak kWh", "Daily cost (€)"]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

    for i, (day, row) in enumerate(daily.iterrows(), start=2):
        ws.cell(row=i, column=1, value=day)
        ws.cell(row=i, column=2, value=float(row["total_kwh"]))
        ws.cell(row=i, column=3, value=float(row["peak_kwh"]))
        ws.cell(row=i, column=4, value=float(row["offpeak_kwh"]))
        # Cost = peak*peak_rate + offpeak*offpeak_rate (rates from Summary sheet)
        ws.cell(row=i, column=5,
                value=f"=C{i}*Summary!$B$4 + D{i}*Summary!$B$5")

    # Totals row
    total_row = len(daily) + 2
    ws.cell(row=total_row, column=1, value="Total").font = KPI_LABEL_FONT
    for col in range(2, 6):
        L = get_column_letter(col)
        ws.cell(row=total_row, column=col,
                value=f"=SUM({L}2:{L}{total_row-1})").font = KPI_LABEL_FONT

    # Formatting
    for r in range(2, total_row + 1):
        for c in (2, 3, 4):
            ws.cell(row=r, column=c).number_format = "#,##0.00"
        ws.cell(row=r, column=5).number_format = '"€"#,##0.00'

    for col_letter, width in [("A",12), ("B",12), ("C",12), ("D",14), ("E",16)]:
        ws.column_dimensions[col_letter].width = width
```

**The key line is the cost formula:** `=C{i}*Summary!$B$4 + D{i}*Summary!$B$5`. That
references the rate cells on the Summary sheet. Change those two cells, every daily
cost updates, the totals update, and the headline cost on the Summary sheet updates.
That's the whole magic of a properly built spreadsheet.

## Step 5.7 — The hourly load-curve sheet (with a chart)

```python
def write_load_curve(ws, month_df):
    ws.title = "Hourly load curve"
    hourly = (month_df["global_active_power"]
              .groupby(month_df.index.hour).mean().round(3))

    ws.append(["Hour of day", "Average active power (kW)"])
    for c in (1, 2):
        cell = ws.cell(row=1, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for i, (hour, kw) in enumerate(hourly.items(), start=2):
        ws.cell(row=i, column=1, value=int(hour))
        ws.cell(row=i, column=2, value=float(kw))
        ws.cell(row=i, column=2).number_format = "0.000"

    # Embed a line chart
    chart = LineChart()
    chart.title = "Average power by hour of day"
    chart.y_axis.title = "Average active power (kW)"
    chart.x_axis.title = "Hour of day"
    chart.height = 10
    chart.width = 18
    data = Reference(ws, min_col=2, min_row=1, max_row=25, max_col=2)
    cats = Reference(ws, min_col=1, min_row=2, max_row=25)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws.add_chart(chart, "D2")

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 26
```

## Step 5.8 — Tie it together and run

Add the `main` function and run it:

```python
def main():
    month_str = sys.argv[1] if len(sys.argv) > 1 else None
    month_str, month_df = load_month(month_str)
    daily = daily_table(month_df)

    wb = Workbook()
    write_summary(wb.active, month_str, daily, n_days=len(daily))
    write_daily(wb.create_sheet(), daily)
    write_load_curve(wb.create_sheet(), month_df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"monthly_energy_report_{month_str}.xlsx"
    wb.save(out_path)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
```

In your terminal, from the project root:
```
python reports\build_monthly_report.py 2008-03
```

**Check:** the script prints `Wrote reports/monthly_energy_report_2008-03.xlsx`.
Open that file in Excel (double-click it). Excel will **automatically recalculate**
all the formulas when it opens — you'll see real numbers everywhere, not raw formula
text.

> Quick gotcha: if you see `#NAME?` errors anywhere, it usually means openpyxl wrote a
> formula but Excel hasn't recalculated yet. Close and reopen the file, or press
> Ctrl+Alt+F9 to force a full recalculation.

**Now the moment of truth — verify the spreadsheet is alive:** click on cell `B4` on
the Summary sheet (the peak rate). Change `0.20` to `0.30`. Watch every cost cell
update — daily costs, monthly total, everything. **That** is what "recurring" and
"dynamic" actually mean.

## Step 5.9 — Prove it's recurring (run for another month)

Run the script again for a different month:
```
python reports\build_monthly_report.py 2009-11
```

A second `.xlsx` appears in `reports/`. Same template, fresh data. That's the
deliverable hiring managers picture when they read "built recurring reports."

Run it once more without any argument:
```
python reports\build_monthly_report.py
```
This time it auto-picks the most recent complete month — the "I'll do the right
thing if you forget to tell me which month" behavior.

## Step 5.10 — Document refresh instructions

Open your project `README.md` (or create it now — even a minimal one). Add a section:

```markdown
## Refresh the monthly report

The monthly energy report is regenerated by running:
~~~
python reports/build_monthly_report.py 2008-03      # explicit month
python reports/build_monthly_report.py              # auto-picks latest complete month
~~~

Output: `reports/monthly_energy_report_<YYYY-MM>.xlsx`. Open in Excel — formulas
recalculate automatically. To change tariff rates, edit the yellow cells (`B4`,
`B5`) on the Summary sheet; all dependent cells update.

To swap in new source data, replace the parquet file at
`data/processed/power_readings_clean.parquet` and re-run.
```

Documenting the refresh procedure is what makes the report genuinely *recurring* and
not just *re-runnable by you*.

## Step 5.11 — Commit Phase 5

```
git add .
git commit -m "Phase 5: recurring monthly Excel report - Summary KPIs, Daily breakdown, Hourly load curve with chart, formula-driven and parameterized"
```

---

## What you've demonstrated

You built a parameterized, formula-driven, multi-sheet Excel report that regenerates
from a single command — and documented how to refresh it. You picked the formula-vs-
hardcoded design deliberately, used the industry-convention yellow shading for
editable cells, and validated the "recurring" property by actually running it twice
for different months.

Your interview line: *"I built a Python-driven monthly energy report in Excel. The
script takes a month as an argument, defaults to the most recent complete month, and
outputs a three-sheet workbook with KPIs, a daily breakdown, and an hourly load curve
with an embedded chart. I made it formula-driven — the tariff rates live in two
editable yellow cells and every cost updates when you change them — so a non-technical
stakeholder can do what-if analysis without touching the code. To refresh, you run one
command; I documented the steps in the README."*

When Phase 5 is committed, come back for Phase 6: the interactive Streamlit dashboard.
