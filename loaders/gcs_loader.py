"""Google Cloud Storage loader for staging weather data."""

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from google.cloud import storage

from config import get_settings

logger = structlog.get_logger(__name__)


class GCSLoader:
    """Uploads weather data to GCS as JSON for staging."""

    def __init__(self):
        settings = get_settings()
        self.client = storage.Client(project=settings.gcp.project_id)
        self.bucket_name = settings.gcs.bucket
        self.prefix = settings.gcs.staging_prefix
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_json(
        self, records: list[dict[str, Any]], partition_key: str | None = None
    ) -> str:
        """Upload records as newline-delimited JSON to GCS.

        Args:
            records: List of dictionaries to upload
            partition_key: Optional partition path (e.g., '2024/01/15/10')

        Returns:
            GCS URI of uploaded file
        """
        if not records:
            logger.warning("no_records_to_upload")
            return ""

        now = datetime.now(timezone.utc)
        partition = partition_key or now.strftime("%Y/%m/%d/%H")
        blob_name = f"{self.prefix}/{partition}/weather_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"

        ndjson = "\n".join(json.dumps(r, default=str) for r in records)
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(ndjson, content_type="application/x-ndjson")

        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
        logger.info("uploaded_to_gcs", uri=gcs_uri, records=len(records))
        return gcs_uri

    def list_blobs(self, prefix: str | None = None) -> list[str]:
        """List blobs in the staging area."""
        prefix = prefix or self.prefix
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [f"gs://{self.bucket_name}/{b.name}" for b in blobs]
