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

st.subheader("Daily energy use")
st.line_chart(daily, height=260, y_label="kWh")

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

