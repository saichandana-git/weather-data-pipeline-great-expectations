{{
    config(materialized='ephemeral')
}}

with hourly as (
    select * from {{ ref('stg_weather_hourly') }}
),

daily as (
    select
        city_name,
        latitude,
        longitude,
        country,
        timezone,
        date(observation_time) as observation_date,

        -- Temperature
        avg(temperature_c) as avg_temp_c,
        min(temperature_c) as min_temp_c,
        max(temperature_c) as max_temp_c,
        max(temperature_c) - min(temperature_c) as temp_range_c,
        avg(feels_like_c) as avg_feels_like_c,

        -- Moisture
        avg(humidity_pct) as avg_humidity_pct,
        sum(precipitation_mm) as total_precipitation_mm,
        sum(rain_mm) as total_rain_mm,
        sum(snowfall_cm) as total_snowfall_cm,

        -- Atmospheric
        avg(pressure_hpa) as avg_pressure_hpa,
        avg(cloud_cover_pct) as avg_cloud_cover_pct,
        avg(visibility_m) as avg_visibility_m,

        -- Wind
        avg(wind_speed_ms) as avg_wind_speed_ms,
        max(wind_speed_ms) as max_wind_speed_ms,
        max(wind_gust_ms) as max_wind_gust_ms,

        -- Solar
        max(uv_index) as max_uv_index,

        -- Quality
        count(*) as observation_count,
        countif(temperature_c is not null) as temp_observation_count

    from hourly
    group by 1, 2, 3, 4, 5, 6
)

select * from daily
