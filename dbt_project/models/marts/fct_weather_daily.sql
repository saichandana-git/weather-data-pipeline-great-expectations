{{
    config(
        materialized='incremental',
        unique_key=['city_name', 'observation_date'],
        partition_by={
            "field": "observation_date",
            "data_type": "date",
            "granularity": "month"
        },
        cluster_by=['city_name', 'country']
    )
}}

with daily as (
    select * from {{ ref('int_weather_daily_agg') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['city_name', 'observation_date']) }} as weather_daily_id,

        city_name,
        country,
        latitude,
        longitude,
        observation_date,

        round(avg_temp_c, 1) as avg_temperature_c,
        round(min_temp_c, 1) as min_temperature_c,
        round(max_temp_c, 1) as max_temperature_c,
        round(temp_range_c, 1) as temperature_range_c,
        round(avg_feels_like_c, 1) as avg_feels_like_c,

        case
            when avg_temp_c < 0 then 'freezing'
            when avg_temp_c < 10 then 'cold'
            when avg_temp_c < 20 then 'mild'
            when avg_temp_c < 30 then 'warm'
            else 'hot'
        end as temperature_category,

        round(avg_humidity_pct, 0) as avg_humidity_pct,
        round(total_precipitation_mm, 1) as total_precipitation_mm,
        round(total_rain_mm, 1) as total_rain_mm,
        round(total_snowfall_cm, 1) as total_snowfall_cm,
        total_precipitation_mm > 0 as had_precipitation,
        total_snowfall_cm > 0 as had_snowfall,

        round(avg_pressure_hpa, 0) as avg_pressure_hpa,
        round(avg_cloud_cover_pct, 0) as avg_cloud_cover_pct,
        round(avg_visibility_m, 0) as avg_visibility_m,

        round(avg_wind_speed_ms, 1) as avg_wind_speed_ms,
        round(max_wind_speed_ms, 1) as max_wind_speed_ms,
        round(max_wind_gust_ms, 1) as max_wind_gust_ms,

        max_uv_index,
        observation_count,
        observation_count >= 20 as is_complete_day

    from daily
)

select * from final

{% if is_incremental() %}
where observation_date > (select max(observation_date) from {{ this }})
{% endif %}
