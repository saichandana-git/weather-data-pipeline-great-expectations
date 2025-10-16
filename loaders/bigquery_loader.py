"""BigQuery loader with schema management."""

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from google.cloud import bigquery

from config import get_settings

logger = structlog.get_logger(__name__)

RAW_TABLE_SCHEMA = [
    bigquery.SchemaField("city_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT64"),
    bigquery.SchemaField("longitude", "FLOAT64"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("timezone", "STRING"),
    bigquery.SchemaField("observation_time", "TIMESTAMP"),
    bigquery.SchemaField("temperature_2m", "FLOAT64"),
    bigquery.SchemaField("relative_humidity_2m", "FLOAT64"),
    bigquery.SchemaField("dew_point_2m", "FLOAT64"),
    bigquery.SchemaField("apparent_temperature", "FLOAT64"),
    bigquery.SchemaField("precipitation", "FLOAT64"),
    bigquery.SchemaField("rain", "FLOAT64"),
    bigquery.SchemaField("snowfall", "FLOAT64"),
    bigquery.SchemaField("snow_depth", "FLOAT64"),
    bigquery.SchemaField("weather_code", "INT64"),
    bigquery.SchemaField("pressure_msl", "FLOAT64"),
    bigquery.SchemaField("surface_pressure", "FLOAT64"),
    bigquery.SchemaField("cloud_cover", "FLOAT64"),
    bigquery.SchemaField("wind_speed_10m", "FLOAT64"),
    bigquery.SchemaField("wind_direction_10m", "FLOAT64"),
    bigquery.SchemaField("wind_gusts_10m", "FLOAT64"),
    bigquery.SchemaField("visibility", "FLOAT64"),
    bigquery.SchemaField("uv_index", "FLOAT64"),
    bigquery.SchemaField("extracted_at", "TIMESTAMP"),
]


class BigQueryLoader:
    """Loads weather data into BigQuery."""

    def __init__(self):
        settings = get_settings()
        self.client = bigquery.Client(project=settings.gcp.project_id)
        self.project = settings.gcp.project_id
        self.raw_dataset = settings.bigquery.raw_dataset
        self.dataset = settings.bigquery.dataset

    def ensure_dataset(self, dataset_id: str) -> None:
        """Create dataset if it doesn't exist."""
        dataset_ref = f"{self.project}.{dataset_id}"
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        self.client.create_dataset(dataset, exists_ok=True)
        logger.info("dataset_ensured", dataset=dataset_id)

    def ensure_raw_table(self) -> str:
        """Create the raw hourly observations table."""
        self.ensure_dataset(self.raw_dataset)
        table_id = f"{self.project}.{self.raw_dataset}.hourly_observations"

        table = bigquery.Table(table_id, schema=RAW_TABLE_SCHEMA)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="observation_time",
        )
        table.clustering_fields = ["city_name", "country"]

        table = self.client.create_table(table, exists_ok=True)
        logger.info("raw_table_ensured", table=table_id)
        return table_id

    def load_from_gcs(self, gcs_uri: str) -> int:
        """Load data from GCS JSON into BigQuery raw table."""
        table_id = self.ensure_raw_table()

        job_config = bigquery.LoadJobConfig(
            schema=RAW_TABLE_SCHEMA,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        load_job = self.client.load_table_from_uri(
            gcs_uri, table_id, job_config=job_config
        )
        result = load_job.result()

        logger.info(
            "bigquery_load_complete",
            table=table_id,
            rows=result.output_rows,
        )
        return result.output_rows

    def load_records(self, records: list[dict[str, Any]]) -> int:
        """Direct load records into BigQuery."""
        table_id = self.ensure_raw_table()

        errors = self.client.insert_rows_json(table_id, records)
        if errors:
            logger.error("bigquery_insert_errors", errors=errors[:5])
            raise RuntimeError(f"BigQuery insert errors: {errors[:5]}")

        logger.info("bigquery_direct_load", rows=len(records))
        return len(records)

    def get_row_count(self, table_ref: str | None = None) -> int:
        """Get row count for monitoring."""
        table_ref = table_ref or f"{self.project}.{self.raw_dataset}.hourly_observations"
        table = self.client.get_table(table_ref)
        return table.num_rows
