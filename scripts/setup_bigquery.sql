-- BigQuery Setup for Weather Pipeline

-- Create raw dataset
CREATE SCHEMA IF NOT EXISTS raw_weather
OPTIONS(location = 'US');

-- Create analytics dataset
CREATE SCHEMA IF NOT EXISTS weather_analytics
OPTIONS(location = 'US');

-- Create raw table
CREATE TABLE IF NOT EXISTS raw_weather.hourly_observations (
    city_name STRING NOT NULL,
    latitude FLOAT64,
    longitude FLOAT64,
    country STRING,
    timezone STRING,
    observation_time TIMESTAMP,
    temperature_2m FLOAT64,
    relative_humidity_2m FLOAT64,
    dew_point_2m FLOAT64,
    apparent_temperature FLOAT64,
    precipitation FLOAT64,
    rain FLOAT64,
    snowfall FLOAT64,
    snow_depth FLOAT64,
    weather_code INT64,
    pressure_msl FLOAT64,
    surface_pressure FLOAT64,
    cloud_cover FLOAT64,
    wind_speed_10m FLOAT64,
    wind_direction_10m FLOAT64,
    wind_gusts_10m FLOAT64,
    visibility FLOAT64,
    uv_index FLOAT64,
    extracted_at TIMESTAMP
)
PARTITION BY DATE(observation_time)
CLUSTER BY city_name, country;
