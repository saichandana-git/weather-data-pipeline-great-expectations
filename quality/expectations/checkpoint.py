"""Great Expectations checkpoint for weather data validation."""

import pandas as pd
import structlog
import great_expectations as gx
from great_expectations.core import ExpectationSuite

from .weather_suite import build_weather_suite

logger = structlog.get_logger(__name__)


class WeatherQualityCheckpoint:
    """Runs Great Expectations validation on weather data batches."""

    def __init__(self):
        self.context = gx.get_context()
        self.suite = build_weather_suite()

    def validate_batch(self, records: list[dict]) -> dict:
        """Validate a batch of weather records.

        Args:
            records: List of weather observation dicts

        Returns:
            Dict with 'success' bool, 'statistics', and 'failed_expectations'
        """
        df = pd.DataFrame(records)
        logger.info("validating_batch", rows=len(df))

        # Create datasource and batch
        datasource = self.context.sources.add_or_update_pandas(name="weather_batch")
        data_asset = datasource.add_dataframe_asset(name="weather_data")
        batch_request = data_asset.build_batch_request(dataframe=df)

        # Run validation
        checkpoint = self.context.add_or_update_checkpoint(
            name="weather_checkpoint",
            validations=[
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": self.suite.expectation_suite_name,
                },
            ],
        )

        # Register suite
        self.context.add_or_update_expectation_suite(
            expectation_suite=self.suite
        )

        result = checkpoint.run()

        # Parse results
        run_results = list(result.run_results.values())
        if not run_results:
            return {"success": False, "statistics": {}, "failed_expectations": ["No results returned"]}

        validation_result = run_results[0]["validation_result"]
        stats = validation_result.statistics

        failed = []
        for r in validation_result.results:
            if not r.success:
                failed.append({
                    "expectation_type": r.expectation_config.expectation_type,
                    "kwargs": r.expectation_config.kwargs,
                    "observed_value": r.result.get("observed_value"),
                })

        outcome = {
            "success": validation_result.success,
            "statistics": {
                "evaluated_expectations": stats["evaluated_expectations"],
                "successful_expectations": stats["successful_expectations"],
                "unsuccessful_expectations": stats["unsuccessful_expectations"],
                "success_percent": stats["success_percent"],
            },
            "failed_expectations": failed,
        }

        if outcome["success"]:
            logger.info("validation_passed", stats=outcome["statistics"])
        else:
            logger.error("validation_failed", failed=failed, stats=outcome["statistics"])

        return outcome
