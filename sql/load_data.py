import pandas as pd
from sqlalchemy import create_engine

# 1. Read the raw file.
#    sep=";"        -> values are semicolon-separated
#    na_values="?"  -> treat every "?" as a missing value (so columns stay numeric)
#    low_memory=False -> read the whole file in one pass for consistent types
df = pd.read_csv(
    "data/raw/household_power_consumption.txt",
    sep=";",
    na_values="?",
    low_memory=False,
)

# 2. Combine Date + Time into a single proper timestamp column.
df["reading_ts"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%d/%m/%Y %H:%M:%S",
)

# 3. Drop the now-redundant columns and tidy the column names to lowercase.
df = df.drop(columns=["Date", "Time"])
df.columns = [c.lower() for c in df.columns]

# 4. Write into a SQLite database file called powerpulse.db.
engine = create_engine("sqlite:///powerpulse.db")
df.to_sql("power_readings", engine, if_exists="replace", index=False)

print(f"Loaded {len(df):,} rows into powerpulse.db")