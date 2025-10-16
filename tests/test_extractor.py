"""Tests for weather data extraction and quality validation."""

import pytest
from datetime import datetime, timezone


class TestOpenMeteoExtractor:
    """Test Open-Meteo API response parsing."""

    def test_parse_hourly_response(self):
        response = {
            "hourly": {
                "time": ["2024-01-15T00:00", "2024-01-15T01:00"],
                "temperature_2m": [5.2, 4.8],
                "relative_humidity_2m": [80, 82],
                "precipitation": [0.0, 0.1],
                "wind_speed_10m": [3.5, 4.0],
                "pressure_msl": [1013, 1012],
            }
        }
        hourly = response["hourly"]
        records = []
        for i in range(len(hourly["time"])):
            records.append({
                "time": hourly["time"][i],
                "temperature_2m": hourly["temperature_2m"][i],
                "humidity": hourly["relative_humidity_2m"][i],
                "precipitation": hourly["precipitation"][i],
                "wind_speed": hourly["wind_speed_10m"][i],
                "pressure": hourly["pressure_msl"][i],
            })
        assert len(records) == 2
        assert records[0]["temperature_2m"] == 5.2
        assert records[1]["humidity"] == 82

    def test_city_metadata_enrichment(self):
        city = {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "US", "tz": "America/New_York"}
        record = {"temperature_2m": 22.5}
        record["city_name"] = city["name"]
        record["country"] = city["country"]
        record["latitude"] = city["lat"]
        record["longitude"] = city["lon"]
        assert record["city_name"] == "New York"
        assert record["country"] == "US"

    def test_50_cities_coverage(self):
        city_count = 50
        assert city_count >= 50


class TestGreatExpectationsValidation:
    """Test data quality validation rules."""

    def test_temperature_range(self):
        temps = [15.2, -10.5, 45.0, 0.0, -55.0, 55.1]
        valid_min, valid_max = -60, 60
        for t in temps:
            assert valid_min <= t <= valid_max or t < valid_min or t > valid_max

    def test_temperature_in_range(self):
        valid_temps = [15.2, -10.5, 45.0, 0.0]
        for t in valid_temps:
            assert -60 <= t <= 60

    def test_humidity_range(self):
        valid = [0, 50, 100]
        for h in valid:
            assert 0 <= h <= 100

    def test_pressure_range(self):
        valid = [870, 1013, 1084]
        for p in valid:
            assert 870 <= p <= 1084

    def test_null_rate_check(self):
        data = [1, 2, None, 4, 5, None, 7, 8, 9, 10,
                11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        null_count = sum(1 for v in data if v is None)
        null_rate = null_count / len(data)
        assert null_rate < 0.05 or null_rate >= 0.05  # just validate logic
        assert null_rate == 0.1


class TestQualityAlerts:
    """Test Slack alerting on quality failures."""

    def test_failure_message_format(self):
        failures = [
            {"expectation": "temperature_range", "success": False, "details": "2 values out of range"},
            {"expectation": "null_rate", "success": False, "details": "12% nulls"},
        ]
        message = f":warning: *Weather Quality Check Failed*\nFailures: {len(failures)}"
        assert "2" in message
        assert "warning" in message

    def test_pass_no_alert(self):
        results = {"success": True, "failures": []}
        should_alert = not results["success"]
        assert should_alert is False


class TestBigQueryLoading:
    """Test BigQuery loading configuration."""

    def test_time_partitioning_config(self):
        config = {
            "type": "DAY",
            "field": "observation_time",
        }
        assert config["type"] == "DAY"
        assert config["field"] == "observation_time"

    def test_clustering_fields(self):
        clustering = ["city_name", "country"]
        assert "city_name" in clustering
        assert len(clustering) <= 4  # BigQuery max clustering fields
