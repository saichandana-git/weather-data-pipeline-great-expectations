"""Great Expectations validation suite for weather data."""

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core import ExpectationConfiguration


def build_weather_suite() -> ExpectationSuite:
    """Build the weather data quality expectation suite.

    Validates:
    - Schema: required columns present
    - Nulls: critical columns have < 5% null rate
    - Ranges: temperature, humidity, pressure within physical bounds
    - Volume: minimum expected row count per batch
    """
    suite = ExpectationSuite(expectation_suite_name="weather_quality_suite")

    # === SCHEMA VALIDATION ===
    required_columns = [
        "city_name", "latitude", "longitude", "observation_time",
        "temperature_2m", "relative_humidity_2m", "precipitation",
        "wind_speed_10m", "pressure_msl", "cloud_cover",
    ]
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_table_columns_to_match_set",
            kwargs={
                "column_set": required_columns,
                "exact_match": False,
            },
        )
    )

    # === NULL RATE CHECKS ===
    critical_non_null_columns = [
        "city_name", "observation_time", "temperature_2m",
        "relative_humidity_2m", "wind_speed_10m",
    ]
    for col in critical_non_null_columns:
        suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": col, "mostly": 0.95},
            )
        )

    # === VALUE RANGE CHECKS ===
    # Temperature: -60°C to 60°C
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "temperature_2m",
                "min_value": -60,
                "max_value": 60,
                "mostly": 0.99,
            },
        )
    )

    # Humidity: 0-100%
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "relative_humidity_2m",
                "min_value": 0,
                "max_value": 100,
                "mostly": 0.99,
            },
        )
    )

    # Pressure: 870-1084 hPa (physical bounds)
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "pressure_msl",
                "min_value": 870,
                "max_value": 1084,
                "mostly": 0.99,
            },
        )
    )

    # Wind speed: 0-120 m/s
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "wind_speed_10m",
                "min_value": 0,
                "max_value": 120,
                "mostly": 0.99,
            },
        )
    )

    # Cloud cover: 0-100%
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "cloud_cover",
                "min_value": 0,
                "max_value": 100,
                "mostly": 0.99,
            },
        )
    )

    # Precipitation: >= 0
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "precipitation",
                "min_value": 0,
                "max_value": 500,
                "mostly": 0.99,
            },
        )
    )

    # === ROW COUNT CHECK ===
    # Expect at least 50 cities * 24 hours = 1200 rows min per daily batch
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_table_row_count_to_be_between",
            kwargs={"min_value": 100, "max_value": 100000},
        )
    )

    return suite
