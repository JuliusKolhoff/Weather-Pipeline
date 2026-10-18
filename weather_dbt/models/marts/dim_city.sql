{{ config(materialized='table') }}

select distinct on (city)
    city,
    latitude,
    longitude,
    elevation_m
from {{ ref('stg_weather_hourly') }}
order by city, ingested_at desc