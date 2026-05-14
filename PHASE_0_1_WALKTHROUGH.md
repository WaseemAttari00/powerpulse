# Phase 0 & 1 — Beginner Walkthrough (from zero)

This assumes you have never used Git, Python, or SQL before. Follow it top to bottom.
Every command is something you type into a **terminal** (explained in Step 0.4).
After each step there is a "Check" — do not move on until the check passes.

When you see a code block, type (or paste) those lines one at a time and press Enter.
Lines starting with `#` are comments — you don't type those.

---

# PHASE 0 — SETUP

## Step 0.1 — Install Python

Python is the programming language you'll use to clean and analyze the data.

1. Go to **python.org/downloads**.
2. Click the big yellow "Download Python 3.x" button.
3. Run the installer. **CRITICAL:** on the first screen, tick the checkbox
   **"Add Python to PATH"** at the bottom before clicking "Install Now".
   If you miss this, Windows won't know where Python is and nothing will work.
4. Let it finish, then close the installer.

**Check:** Open a terminal (see Step 0.4) and type:
```
python --version
```
You should see something like `Python 3.12.x`. If you get "command not found" or
nothing, Python isn't on your PATH — re-run the installer and choose "Modify", then
enable "Add to PATH". On some systems the command is `py` instead of `python`.

## Step 0.2 — Install Git

Git is the tool that tracks every change you make and lets you publish to GitHub.

1. Go to **git-scm.com/download/win** — the download starts automatically.
2. Run the installer. You can click "Next" through every screen — the defaults are fine.

**Check:**
```
git --version
```
You should see `git version 2.x.x`.

## Step 0.3 — Install a code editor (VS Code)

You need somewhere to write and read code files. VS Code is free and the standard choice.

1. Go to **code.visualstudio.com**, download, install with defaults.
2. Open VS Code. Go to the Extensions panel (the four-squares icon on the left) and
   install the **Python** extension by Microsoft. This gives you Jupyter notebook
   support later.

## Step 0.4 — Open a terminal

A terminal is a window where you type commands instead of clicking buttons.

The easiest one to use: open **VS Code**, then from the top menu choose
**Terminal → New Terminal**. A panel opens at the bottom. That's your terminal.
On Windows it will be "PowerShell" — that's fine.

Two commands you'll use constantly:
- `cd <foldername>` — "change directory", i.e. move into a folder.
- `cd ..` — move up one folder.
- `ls` (or `dir`) — list what's in the current folder.

## Step 0.5 — Go to your project folder

You already have a folder on your Desktop called **Data Science Project**. Build the
project right there. In the terminal:
```
cd "$HOME\Desktop\Data Science Project"
```
The quotes matter because the folder name has spaces.

**Check:** type `ls` — you should see `PROJECT_GUIDE.md` and this walkthrough file
listed.

## Step 0.6 — Initialize Git

This turns the folder into a Git repository — from now on Git watches it for changes.
```
git init
```

**Check:** you'll see `Initialized empty Git repository...`. A hidden `.git` folder
now exists (you won't normally see it).

## Step 0.7 — Create a virtual environment

A "virtual environment" (venv) is an isolated box for this project's Python packages,
so they don't clash with anything else on your computer. Reviewers expect to see one.
```
python -m venv venv
```
This creates a folder called `venv`. It takes a few seconds.

Now **activate** it:
```
venv\Scripts\activate
```

**Check:** your terminal prompt now starts with `(venv)`. That means the box is active.

> **If you get a red error about "running scripts is disabled on this system":**
> PowerShell blocks scripts by default. Fix it once by running:
> ```
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Type `Y` to confirm, then try `venv\Scripts\activate` again.

From now on, **always activate the venv** (`venv\Scripts\activate`) when you open a
new terminal for this project.

## Step 0.8 — Install the Python packages

`pip` is Python's package installer. These are the libraries the project needs:
```
pip install pandas numpy matplotlib seaborn jupyter sqlalchemy streamlit openpyxl
```
This downloads a lot — give it a minute or two.

What each one is for, roughly: **pandas** = working with tables of data;
**numpy** = number crunching; **matplotlib / seaborn** = charts;
**jupyter** = notebooks; **sqlalchemy** = talking to the database from Python;
**streamlit** = the dashboard app; **openpyxl** = writing Excel files.

Now record exactly what you installed, so anyone can reproduce it:
```
pip freeze > requirements.txt
```

**Check:** `ls` shows a new `requirements.txt` file.

## Step 0.9 — Create the folder structure

These commands make the empty folders the project will fill in later:
```
mkdir data, data\raw, data\processed, sql, notebooks, reports, app
```

**Check:** `ls` shows the new folders.

## Step 0.10 — Create the .gitignore file

A `.gitignore` file tells Git which things to **never** track — big files, the venv,
temporary junk. Create a file named exactly `.gitignore` in the project folder (you
can do this in VS Code: File → New File, save as `.gitignore`). Put this inside:
```
venv/
data/raw/
data/processed/
*.ipynb_checkpoints
powerpulse.db
__pycache__/
```
Why exclude `data/raw/`? The dataset is ~130 MB — too big for Git, and committing
large data files is considered bad practice. Your README will tell people where to
download it instead.

## Step 0.11 — Your first commit

A "commit" is a saved snapshot of your project. Make the first one:
```
git add .
git commit -m "Phase 0: project setup, environment, folder structure"
```
`git add .` stages everything (except what's in `.gitignore`); `git commit` saves the
snapshot with a message describing it.

**Check:** `git log` shows one commit with your message. Press `q` to exit the log view.

**Phase 0 is done.** You now have a real, professional project skeleton.

---

# PHASE 1 — GET THE DATA INTO SQL

## Step 1.1 — Download the dataset

1. Go to the **UCI Machine Learning Repository** and search for
   **"Individual household electric power consumption"** (it's dataset #235).
2. On the dataset page, click **"Download"** — you get a `.zip` file.
3. Unzip it. Inside is a file called `household_power_consumption.txt`.
4. Move that `.txt` file into your project's `data\raw\` folder.

**Check:** the file exists at `data\raw\household_power_consumption.txt` and is
roughly 130 MB.

## Step 1.2 — Look at the raw data with your own eyes

Before writing any code, understand what you're dealing with. Open the `.txt` file in
VS Code (it may take a moment — it's large). Look at the first few lines. Notice:
- The first line is the **header** (column names).
- Values are separated by **semicolons** (`;`), not commas.
- `Date` and `Time` are **two separate columns**.
- Some values are a literal **`?`** — those are missing readings.

Writing down what you observe *before* coding is a real analyst habit. It's also a
great interview line: "the first thing I did was inspect the raw file."

## Step 1.3 — Write the SQL schema

A "schema" defines the table that will hold the data. In VS Code, create a new file
`sql\01_create_schema.sql` with this content:
```sql
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
```
`REAL` means a decimal number; `TEXT` means text. We store the timestamp as text in
ISO format (`2006-12-16 17:24:00`) — SQLite sorts and filters that correctly.

## Step 1.4 — Write the load script

This Python script reads the raw `.txt`, fixes the date and the `?` values, and loads
everything into a SQLite database file. Create `sql\load_data.py`:
```python
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
```

Why do the date/`?` handling in Python instead of pure SQL? Because pandas makes these
two specific fixes one line each, and doing the messy parts in one clear place is
easier to explain later. The *analysis* will still be done in SQL.

## Step 1.5 — Run the load script

In the terminal (venv still active — prompt shows `(venv)`):
```
python sql\load_data.py
```
It reads 2 million rows, so give it 10–30 seconds.

**Check:** it prints `Loaded 2,075,259 rows into powerpulse.db`, and `ls` shows a new
`powerpulse.db` file.

## Step 1.6 — Sanity-check the data

Never trust a load until you've verified it. Two ways to look at your database:

**Option A — a free GUI (easiest for a beginner).** Download **DB Browser for SQLite**
(sqlitebrowser.org), open `powerpulse.db` with it, and you can click through the table
and run queries in the "Execute SQL" tab.

**Option B — from Python.** Create `sql\sanity_check.py`:
```python
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
```
Run it: `python sql\sanity_check.py`

**Check — you should see:**
- Row count = **2,075,259**
- Date range from **2006-12-16** to **2010-11-26**
- Missing active-power readings ≈ **25,979** (a small but real chunk — this is your
  data-quality story starting to appear; you'll dig into it in Phase 2)

## Step 1.7 — Commit Phase 1

```
git add .
git commit -m "Phase 1: load household power data into SQLite, add sanity checks"
```

**Phase 1 is done.** You have ~2 million rows of real data in a queryable SQL database,
loaded reproducibly, and verified.

---

## What you've demonstrated so far

Even just through these two phases you can already say, truthfully: you set up a
reproducible Python environment, designed a SQL schema with a deliberate timestamp
design choice, wrote a load pipeline that handles malformed dates and missing values,
and verified the load before trusting it. That last part — *verifying before
trusting* — is exactly the "data accuracy and validation" mindset the job posting asks
for.

When both phases are done and your sanity checks pass, come back and we'll do Phase 2:
cleaning and validation, which is where your strongest interview material comes from.
