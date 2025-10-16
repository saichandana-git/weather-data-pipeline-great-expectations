"""Prefect flow: Weather data pipeline with quality gates."""

import asyncio
from datetime import datetime, timezone

import structlog
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash

from extractors import OpenMeteoExtractor
from loaders import GCSLoader, BigQueryLoader
from quality.expectations.checkpoint import WeatherQualityCheckpoint
from quality.alerts import send_quality_alert, send_success_notification

logger = structlog.get_logger(__name__)


@task(retries=2, retry_delay_seconds=30, log_prints=True)
def extract_weather_data(days: int = 1) -> list[dict]:
    """Extract hourly weather from Open-Meteo API."""
    extractor = OpenMeteoExtractor()
    records = asyncio.run(extractor.extract_all(days=days))
    print(f"Extracted {len(records)} weather records")
    return records


@task(retries=1, log_prints=True)
def upload_to_gcs(records: list[dict]) -> str:
    """Stage data in GCS."""
    loader = GCSLoader()
    gcs_uri = loader.upload_json(records)
    print(f"Uploaded to {gcs_uri}")
    return gcs_uri


@task(retries=1, log_prints=True)
def load_to_bigquery(gcs_uri: str) -> int:
    """Load from GCS into BigQuery raw table."""
    loader = BigQueryLoader()
    rows = loader.load_from_gcs(gcs_uri)
    print(f"Loaded {rows} rows to BigQuery")
    return rows


@task(log_prints=True)
def validate_data_quality(records: list[dict]) -> dict:
    """Run Great Expectations validation suite.

    Returns validation result dict. If validation fails,
    this task still succeeds — the flow decides whether to halt.
    """
    checkpoint = WeatherQualityCheckpoint()
    result = checkpoint.validate_batch(records)
    print(f"Validation: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Stats: {result['statistics']}")
    return result


@task(log_prints=True)
def handle_quality_failure(validation_result: dict) -> None:
    """Send Slack alert and halt pipeline."""
    send_quality_alert(validation_result)
    print("Quality failure alert sent to Slack")


@task(log_prints=True)
def run_dbt_transformations() -> None:
    """Execute dbt run and test."""
    import subprocess

    dbt_dir = "dbt_project"

    # dbt run
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--target", "prod"],
        cwd=dbt_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed:\n{result.stderr}")
    print(f"dbt run output:\n{result.stdout[-500:]}")

    # dbt test
    result = subprocess.run(
        ["dbt", "test", "--profiles-dir", ".", "--target", "prod"],
        cwd=dbt_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt test failed:\n{result.stderr}")
    print(f"dbt test output:\n{result.stdout[-500:]}")


@flow(name="weather-data-pipeline", log_prints=True)
def weather_pipeline(days: int = 1):
    """Main weather pipeline flow.

    Steps:
    1. Extract weather data from Open-Meteo API
    2. Upload to GCS staging
    3. Load into BigQuery raw table
    4. Validate with Great Expectations
    5. If validation passes → run dbt transformations
    6. If validation fails → alert Slack and HALT
    """
    print(f"Starting weather pipeline at {datetime.now(timezone.utc).isoformat()}")

    # Step 1: Extract
    records = extract_weather_data(days=days)

    # Step 2: Stage in GCS
    gcs_uri = upload_to_gcs(records)

    # Step 3: Load to BigQuery
    load_to_bigquery(gcs_uri)

    # Step 4: Validate quality
    validation_result = validate_data_quality(records)

    # Step 5: Quality gate
    if not validation_result["success"]:
        handle_quality_failure(validation_result)
        raise RuntimeError(
            f"Data quality check FAILED. "
            f"{validation_result['statistics'].get('unsuccessful_expectations', 0)} "
            f"expectations failed. Pipeline halted."
        )

    # Step 6: Transform with dbt
    send_success_notification()
    run_dbt_transformations()

    print("Weather pipeline completed successfully!")


if __name__ == "__main__":
    weather_pipeline()
