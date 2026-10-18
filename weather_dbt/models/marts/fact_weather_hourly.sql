{{ config(materialized='table') }}

with ranked as (

    select
        *,
        row_number() over (
            partition by city, observed_at
            order by ingested_at desc
        ) as rn
    from {{ ref('stg_weather_hourly') }}
    where observed_at <= ingested_at      -- drop forecast hours, keep what has happened

)

select
    city,
    observed_at,
    temperature_c,
    humidity_pct,
    precipitation_mm,
    wind_speed_kmh,
    weather_code
from ranked
where rn = 1