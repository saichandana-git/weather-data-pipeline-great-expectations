with source as (
    select * from {{ source('raw_weather', 'hourly_observations') }}
),

cleaned as (
    select
        city_name,
        latitude,
        longitude,
        country,
        timezone,
        observation_time,

        -- Temperature
        temperature_2m as temperature_c,
        apparent_temperature as feels_like_c,
        dew_point_2m as dew_point_c,

        -- Moisture
        relative_humidity_2m as humidity_pct,
        precipitation as precipitation_mm,
        rain as rain_mm,
        snowfall as snowfall_cm,
        snow_depth as snow_depth_m,

        -- Atmospheric
        pressure_msl as pressure_hpa,
        surface_pressure as surface_pressure_hpa,
        cloud_cover as cloud_cover_pct,
        visibility as visibility_m,

        -- Wind
        wind_speed_10m as wind_speed_ms,
        wind_direction_10m as wind_direction_deg,
        wind_gusts_10m as wind_gust_ms,

        -- Solar
        uv_index,
        weather_code,

        -- Metadata
        extracted_at,

        -- Dedup
        row_number() over (
            partition by city_name, observation_time
            order by extracted_at desc
        ) as _row_num

    from source
    where observation_time is not null
      and city_name is not null
)

select * from cleaned
where _row_num = 1
