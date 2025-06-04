{{
    config(materialized='table')
}}

with city_data as (
    select distinct
        city_name,
        latitude,
        longitude,
        country,
        timezone
    from {{ ref('stg_weather_hourly') }}
),

enriched as (
    select
        city_name,
        latitude,
        longitude,
        country,
        timezone,
        case
            when latitude between -23.5 and 23.5 then 'tropical'
            when latitude between 23.5 and 35 or latitude between -35 and -23.5 then 'subtropical'
            when latitude between 35 and 55 or latitude between -55 and -35 then 'temperate'
            when latitude between 55 and 66.5 or latitude between -66.5 and -55 then 'subarctic'
            else 'polar'
        end as climate_zone,
        case
            when latitude >= 0 then 'northern'
            else 'southern'
        end as hemisphere
    from city_data
)

select * from enriched
