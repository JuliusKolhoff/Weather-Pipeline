{{ config(materialized='table') }}

select
    city,
    (observed_at at time zone 'Europe/Berlin')::date as day,
    round(avg(temperature_c), 1)   as avg_temp_c,
    min(temperature_c)             as min_temp_c,
    max(temperature_c)             as max_temp_c,
    round(sum(precipitation_mm), 1) as total_precip_mm,
    round(avg(wind_speed_kmh), 1)  as avg_wind_kmh,
    count(*)                       as hours_observed
from {{ ref('fact_weather_hourly') }}
group by 1, 2