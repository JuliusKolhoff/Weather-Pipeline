from dotenv import load_dotenv
import os
import requests
from psycopg.types.json import Jsonb
import psycopg

CITIES = {
    "dortmund": (51.5136, 7.4653),
    "hamburg":  (53.5511, 9.9937),
    "berlin":   (52.5200, 13.4050),
    "munich":   (48.1351, 11.5820),
    "cologne":  (50.9375, 6.9603),
}

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]

URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "UTC",
        "past_days": 1,
        "forecast_days": 1,
    }
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def get_conn():
    conn_str = os.getenv("DB_CONNECT_STR")
    conn_str = conn_str if conn_str is not None else exit("Cannot Connect: no env var for DB_CONNECT_STR")
    return psycopg.connect(conn_str)

def get_all_rows(cursor) -> str:
    cursor.execute("""SELECT
    r.city,
    t.value::timestamp        AS observed_at,
    temp.value::numeric       AS temperature_2m
FROM raw.weather_api_response r
CROSS JOIN LATERAL jsonb_array_elements_text(r.payload->'hourly'->'time')
        WITH ORDINALITY AS t(value, idx)
JOIN LATERAL jsonb_array_elements_text(r.payload->'hourly'->'temperature_2m')
        WITH ORDINALITY AS temp(value, idx) ON temp.idx = t.idx
LIMIT 20;""")
    return cursor.fetchall()


def main():
    load_dotenv()


    with get_conn() as conn, conn.cursor() as cur:
        for city, (lat, lon) in CITIES.items():
            data = fetch_weather(lat, lon)
            cur.execute(
                "INSERT INTO raw.weather_api_response (city, payload) VALUES (%s, %s)",
                (city, Jsonb(data)),
            )
            print(f"{city}: {len(data['hourly']['time'])} hours loaded")
        for row in get_all_rows(cur):
            print(row)


if __name__ == "__main__":
    main()