import os
import pandas as pd
import psycopg
import streamlit as st
import altair as alt
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

st.set_page_config(page_title="German Weather", layout="wide")

@st.cache_data(ttl=300)  # re-query at most every 5 minutes
def query(sql) -> pd.DataFrame:
    with psycopg.connect(os.environ["DB_CONNECT_STR"]) as conn, conn.cursor() as cur:
        cur.execute(sql)
        if cur.description  is not None:
            cur.execute(sql)
            cols = [c.name for c in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=cols)

            for c in df.columns:
                if len(df) and isinstance(df[c].iloc[0], Decimal):
                    df[c] = df[c].astype(float)
            return df
        else:
            print("Empty Descriptions")
            return pd.DataFrame()

#Querries/DAtA
hourly = query("""
    select city, observed_at, temperature_c, precipitation_mm, wind_speed_kmh
    from analytics.fact_weather_hourly
""")
daily = query("select * from analytics.fact_weather_daily")

if daily.empty:
    st.warning("No data yet. Run the loader and `dbt run` first.")
    st.stop()

daily["day"] = pd.to_datetime(daily["day"])
hourly["observed_at"] = pd.to_datetime(hourly["observed_at"])

forecast = query("""
    select city, forecast_for, temperature_c, precipitation_mm
    from analytics.fact_weather_forecast
""")


#Sidebar
st.sidebar.header("Filters")
all_cities = sorted(daily["city"].unique())
cities = st.sidebar.multiselect("Cities", all_cities, default=all_cities)

min_day, max_day = daily["day"].min().date(), daily["day"].max().date()
date_range = st.sidebar.date_input(
    "Date range", (min_day, max_day), min_value=min_day, max_value=max_day
)
if len(date_range) != 2:
    st.stop()  # user is still picking the end date
start, end = [pd.Timestamp(d) for d in date_range]

d = daily[daily["city"].isin(cities) & daily["day"].between(start, end)]
h = hourly[
    hourly["city"].isin(cities)
    & hourly["observed_at"].dt.tz_localize(None).between(start, end + pd.Timedelta(days=1))
]

# Charts/Stats
st.title("Weather Data")

if d.empty:
    st.info("No data for this selection.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Average temperature", f"{d['avg_temp_c'].mean():.1f} °C")
k2.metric("Total rainfall", f"{d['total_precip_mm'].sum():.0f} mm")
k3.metric("Days in selection", d["day"].nunique())

st.subheader("Hourly temperature (last 7 days of selection)")
recent = h[h["observed_at"] >= h["observed_at"].max() - pd.Timedelta(days=7)]
st.line_chart(recent.pivot(index="observed_at", columns="city", values="temperature_c"))

st.subheader("Hourly rain (last 7 days of selection)")
recent = h[h["observed_at"] >= h["observed_at"].max() - pd.Timedelta(days=7)]
st.line_chart(recent.pivot(index="observed_at", columns="city", values="precipitation_mm"))

st.subheader("16-day temperature forecast")
if forecast.empty:
    st.info("No forecast data yet.")
else:
    f = forecast[forecast["city"].isin(cities)]
    fc = (
        alt.Chart(f)
        .mark_line()
        .encode(
            x=alt.X("forecast_for:T", title=None),
            y=alt.Y("temperature_c:Q", title="°C", scale=alt.Scale(zero=False)),
            color=alt.Color("city:N", title="City"),
            tooltip=["city", "forecast_for:T", "temperature_c:Q", "precipitation_mm:Q"],
        )
    )
    st.altair_chart(fc, width="stretch")