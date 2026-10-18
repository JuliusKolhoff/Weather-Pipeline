with raw as (

    select id, city, ingested_at, payload
    from {{ source('raw', 'weather_api_response') }}

),

unpacked as (

    select
        r.id          as raw_id,
        r.city,
        r.ingested_at,
        r.payload,
        t.value       as time_str,
        (t.idx - 1)::int as i      -- array position, 0-based
    from raw r
    cross join lateral jsonb_array_elements_text(r.payload->'hourly'->'time')
        with ordinality as t(value, idx)

)

select
    raw_id,
    city,
    ingested_at,
    (time_str::timestamp at time zone 'UTC')                       as observed_at,
    (payload->'hourly'->'temperature_2m'->>i)::numeric             as temperature_c,
    (payload->'hourly'->'relative_humidity_2m'->>i)::numeric       as humidity_pct,
    (payload->'hourly'->'precipitation'->>i)::numeric              as precipitation_mm,
    (payload->'hourly'->'wind_speed_10m'->>i)::numeric             as wind_speed_kmh,
    (payload->'hourly'->'weather_code'->>i)::int                   as weather_code,
    (payload->>'latitude')::numeric                                as latitude,
    (payload->>'longitude')::numeric                               as longitude,
    (payload->>'elevation')::numeric                               as elevation_m
from unpacked