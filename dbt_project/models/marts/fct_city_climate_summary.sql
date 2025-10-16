{{
    config(materialized='table')
}}

with daily as (
    select * from {{ ref('fct_weather_daily') }}
    where observation_date >= date_sub(current_date(), interval 30 day)
),

summary as (
    select
        city_name,
        country,
        latitude,
        longitude,

        count(*) as days_observed,

        round(avg(avg_temperature_c), 1) as avg_temp_30d,
        round(min(min_temperature_c), 1) as min_temp_30d,
        round(max(max_temperature_c), 1) as max_temp_30d,

        round(avg(avg_humidity_pct), 0) as avg_humidity_30d,
        round(sum(total_precipitation_mm), 1) as total_precip_30d,
        countif(had_precipitation) as rainy_days_30d,
        countif(had_snowfall) as snowy_days_30d,

        round(avg(avg_wind_speed_ms), 1) as avg_wind_30d,
        round(max(max_wind_gust_ms), 1) as max_gust_30d,

        round(avg(avg_cloud_cover_pct), 0) as avg_cloud_cover_30d,
        round(avg(max_uv_index), 1) as avg_max_uv_30d,

        -- Comfort index (simple)
        round(
            100
            - abs(avg(avg_temperature_c) - 22) * 2
            - avg(avg_humidity_pct) * 0.3
            - avg(avg_wind_speed_ms) * 1.5
        , 1) as comfort_index

    from daily
    group by 1, 2, 3, 4
)

select * from summary
