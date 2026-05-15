import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///powerpulse.db")

def run(label, query):
    print(f"\n--- {label} ---")
    print(pd.read_sql(query, engine))

run("Row count", "SELECT COUNT(*) AS rows FROM power_readings;")
run("First 5 rows", "SELECT * FROM power_readings LIMIT 5;")
run("Date range", "SELECT MIN(reading_ts) AS first, MAX(reading_ts) AS last FROM power_readings;")
run("Missing active-power readings",
    "SELECT COUNT(*) AS missing FROM power_readings WHERE global_active_power IS NULL;")