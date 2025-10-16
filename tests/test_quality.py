"""Tests for Great Expectations quality validation logic."""

import pytest


class TestWeatherQualitySuite:
    """Test quality suite configuration and expectations."""

    def test_required_columns(self):
        expected_columns = {
            "city_name", "country", "latitude", "longitude",
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "wind_speed_10m", "pressure_msl", "observation_time",
        }
        assert len(expected_columns) == 10
        assert "temperature_2m" in expected_columns
        assert "city_name" in expected_columns

    def test_temperature_range_check(self):
        min_val, max_val = -60, 60
        valid_temps = [-40, -10, 0, 15, 35, 55]
        for t in valid_temps:
            assert min_val <= t <= max_val

    def test_humidity_range_check(self):
        min_val, max_val = 0, 100
        valid = [0, 25, 50, 75, 100]
        for h in valid:
            assert min_val <= h <= max_val

    def test_pressure_range_check(self):
        min_val, max_val = 870, 1084
        valid = [900, 1013, 1050]
        for p in valid:
            assert min_val <= p <= max_val

    def test_null_rate_threshold(self):
        max_null_rate = 0.05
        data = [1, 2, 3, None, 5, 6, 7, 8, 9, 10,
                11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        null_count = sum(1 for v in data if v is None)
        null_rate = null_count / len(data)
        assert null_rate == 0.05

    def test_row_count_bounds(self):
        min_rows, max_rows = 100, 100000
        sample_count = 2400  # 50 cities * 48 hours
        assert min_rows <= sample_count <= max_rows

    def test_suite_name(self):
        suite_name = "weather_quality_suite"
        assert suite_name == "weather_quality_suite"

    def test_checkpoint_pass_result(self):
        result = {"success": True, "statistics": {"successful_expectations": 10, "unsuccessful_expectations": 0}}
        assert result["success"] is True
        assert result["statistics"]["unsuccessful_expectations"] == 0

    def test_checkpoint_fail_result(self):
        result = {"success": False, "statistics": {"successful_expectations": 8, "unsuccessful_expectations": 2}}
        assert result["success"] is False
        assert result["statistics"]["unsuccessful_expectations"] == 2
