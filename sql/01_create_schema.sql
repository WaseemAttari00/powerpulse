-- Defines the table that stores every meter reading.
-- Design choice: Date + Time are combined into ONE timestamp column (reading_ts)
-- because every analysis groups or sorts by time.
DROP TABLE IF EXISTS power_readings;

CREATE TABLE power_readings (
    reading_ts             TEXT,   -- combined date + time, ISO format
    global_active_power    REAL,   -- household real power, kW
    global_reactive_power  REAL,   -- reactive power, kW
    voltage                REAL,   -- volts
    global_intensity       REAL,   -- current, amps
    sub_metering_1         REAL,   -- kitchen, watt-hours
    sub_metering_2         REAL,   -- laundry room, watt-hours
    sub_metering_3         REAL    -- water heater + AC, watt-hours
);