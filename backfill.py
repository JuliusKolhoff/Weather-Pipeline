import os
import time
from datetime import date, timedelta

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import Json

load_dotenv()

CITIES = {
    "dortmund": (51.5136, 7.4653),
    "hamburg":  (53.5511, 9.9937),
    "berlin":   (52.5200, 13.4050),
    "munich":   (48.1351, 11.5820),
    "cologne":  (50.9375, 6.9603),
}
HOURLY_VARS = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
URL = "https://archive-api.open-meteo.com/v1/archive"

START_YEAR = 2020
LATEST = date.today() - timedelta(days=5)


def year_chunks(start_year: int, latest: date):
    for y in range(start_year, latest.year + 1):
        start = date(y, 1, 1)
        end = min(date(y, 12, 31), latest)
        yield start, end


def already_loaded(cur, city: str, start: date) -> bool:
    cur.execute(
        """
        SELECT 1 FROM raw.weather_api_response
        WHERE city = %s AND payload->'hourly'->'time'->>0 = %s
        LIMIT 1
        """,
        (city, f"{start.isoformat()}T00:00"),
    )
    return cur.fetchone() is not None


def fetch(lat, lon, start: date, end: date) -> dict:
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": HOURLY_VARS, "timezone": "UTC",
    }
    for attempt in range(5):
        r = requests.get(URL, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(30 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Rate limit: try again later")


def main():
    with psycopg2.connect(os.environ["DB_CONNECT_STR"]) as conn, conn.cursor() as cur:
        for city, (lat, lon) in CITIES.items():
            for start, end in year_chunks(START_YEAR, LATEST):
                if already_loaded(cur, city, start):
                    print(f"{city} {start.year}: skipped (already loaded)")
                    continue
                data = fetch(lat, lon, start, end)
                cur.execute(
                    "INSERT INTO raw.weather_api_response (city, payload) VALUES (%s, %s)",
                    (city, Json(data)),
                )
                conn.commit()
                print(f"{city} {start.year}: {len(data['hourly']['time'])} hours")
                time.sleep(1)


if __name__ == "__main__":
    main()