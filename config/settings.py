"""Centralized configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class GCPSettings(BaseSettings):
    project_id: str = Field(..., alias="GCP_PROJECT_ID")
    location: str = Field("US", alias="GCP_LOCATION")
    credentials_path: str = Field("", alias="GOOGLE_APPLICATION_CREDENTIALS")
    model_config = {"env_file": ".env", "extra": "ignore"}


class BigQuerySettings(BaseSettings):
    dataset: str = Field("weather_analytics", alias="BIGQUERY_DATASET")
    raw_dataset: str = Field("raw_weather", alias="BIGQUERY_RAW_DATASET")
    model_config = {"env_file": ".env", "extra": "ignore"}


class GCSSettings(BaseSettings):
    bucket: str = Field(..., alias="GCS_BUCKET")
    staging_prefix: str = Field("raw", alias="GCS_STAGING_PREFIX")
    model_config = {"env_file": ".env", "extra": "ignore"}


class SlackSettings(BaseSettings):
    webhook_url: str = Field("", alias="SLACK_WEBHOOK_URL")
    model_config = {"env_file": ".env", "extra": "ignore"}


class Settings(BaseSettings):
    gcp: GCPSettings = GCPSettings()
    bigquery: BigQuerySettings = BigQuerySettings()
    gcs: GCSSettings = GCSSettings()
    slack: SlackSettings = SlackSettings()
    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
