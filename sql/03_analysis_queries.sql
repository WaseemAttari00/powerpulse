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