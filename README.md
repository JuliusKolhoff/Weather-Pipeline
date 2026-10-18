## Weather Data Pipeline

An end-to-end data engineering project: raw API data → PostgreSQL → dbt transformations → Streamlit dashboard.

**Stack:** Python · PostgreSQL · dbt · Streamlit · Altair · pandas · psycopg 3

![alt text](image-2.png)

![alt text](image.png)

---

## What it does

The pipeline pulls hourly weather data and a 16-day forecast for five German cities (Dortmund, Hamburg, Berlin, Munich, Cologne) from the free [Open-Meteo API](https://open-meteo.com/), stores the untouched API responses in Postgres, models them into analytics-ready tables with dbt, and serves them in a filterable dashboard.

```
Open-Meteo API ──► Python loader ──► Postgres (raw) ──► dbt ──► Postgres (analytics) ──► Streamlit
```

## Highlights

- **ELT-Pipeline:** Full API responses are landed as `JSONB` in a `raw` schema first, then transformed inside the warehouse. Raw data stays replayable.
- **Organized into multiple schemes.** `raw` schema for source payloads, `analytics` schema for modelled fact tables (`fact_weather_hourly`, `fact_weather_daily`, `fact_weather_forecast`).
- **Interactive dashboard.** City and date-range filters, average temperature, total rainfall, days selected, hourly temperature and rainfall charts, and a 16-day forecast chart with tooltips.
- **Query caching.** Dashboard queries are cached for 5 minutes to keep the UI fast and the database load low.
- **Secure configuration.** Database credentials are read from environment variables (`.env`), never hardcoded.


## Getting started

### Prerequisites

- Python 3.10+
- PostgreSQL
- dbt (with the Postgres adapter)

### Setup

```bash
git clone https://github.com/JuliusKolhoff/Weather-Pipeline.git
cd Weather-Pipeline

python -m venv .venv
source .venv/bin/activate

pip install requests psycopg[binary] python-dotenv pandas streamlit altair dbt-postgres
```

Create a `.env` file in the project root:

```env
DB_CONNECT_STR=dbname=<dbname> user=<username> password=<password> host=<host> port=<port>
```

Create the raw table:

```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.weather_api_response (
    city        text NOT NULL,
    payload     jsonb NOT NULL,
    loaded_at   timestamptz DEFAULT now()
);
```

### Run the pipeline

```bash
# 1. Load raw data
python main.py

# 2. Transform with dbt
cd weather_dbt
dbt run
cd ..

# 3. Launch the dashboard
streamlit run dashboard.py
```


## Data source

Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).

## Author

**Julius Kolhoff**
