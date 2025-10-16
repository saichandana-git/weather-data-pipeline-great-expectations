"""Open-Meteo API extractor — free, no API key required."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "snowfall",
    "snow_depth",
    "weather_code",
    "pressure_msl",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "visibility",
    "uv_index",
]

CITIES = [
    {"name": "New York", "lat": 40.7128, "lon": -74.006, "country": "US", "tz": "America/New_York"},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "country": "US", "tz": "America/Los_Angeles"},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "country": "US", "tz": "America/Chicago"},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "country": "US", "tz": "America/Chicago"},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.074, "country": "US", "tz": "America/Phoenix"},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "country": "US", "tz": "America/Los_Angeles"},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "country": "US", "tz": "America/Los_Angeles"},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903, "country": "US", "tz": "America/Denver"},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918, "country": "US", "tz": "America/New_York"},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589, "country": "US", "tz": "America/New_York"},
    {"name": "Atlanta", "lat": 33.749, "lon": -84.388, "country": "US", "tz": "America/New_York"},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.797, "country": "US", "tz": "America/Chicago"},
    {"name": "Portland", "lat": 45.5152, "lon": -122.6784, "country": "US", "tz": "America/Los_Angeles"},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431, "country": "US", "tz": "America/Chicago"},
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816, "country": "US", "tz": "America/Chicago"},
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "GB", "tz": "Europe/London"},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "FR", "tz": "Europe/Paris"},
    {"name": "Berlin", "lat": 52.52, "lon": 13.405, "country": "DE", "tz": "Europe/Berlin"},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "JP", "tz": "Asia/Tokyo"},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "AU", "tz": "Australia/Sydney"},
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "country": "CA", "tz": "America/Toronto"},
    {"name": "Mumbai", "lat": 19.076, "lon": 72.8777, "country": "IN", "tz": "Asia/Kolkata"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "country": "SG", "tz": "Asia/Singapore"},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "AE", "tz": "Asia/Dubai"},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.978, "country": "KR", "tz": "Asia/Seoul"},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "country": "MX", "tz": "America/Mexico_City"},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "country": "TH", "tz": "Asia/Bangkok"},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "country": "TR", "tz": "Europe/Istanbul"},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "EG", "tz": "Africa/Cairo"},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792, "country": "NG", "tz": "Africa/Lagos"},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "country": "AR", "tz": "America/Argentina/Buenos_Aires"},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "country": "ZA", "tz": "Africa/Johannesburg"},
    {"name": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "country": "NL", "tz": "Europe/Amsterdam"},
    {"name": "Stockholm", "lat": 59.3293, "lon": 18.0686, "country": "SE", "tz": "Europe/Stockholm"},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6176, "country": "RU", "tz": "Europe/Moscow"},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "country": "CN", "tz": "Asia/Shanghai"},
    {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "country": "HK", "tz": "Asia/Hong_Kong"},
    {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "country": "ID", "tz": "Asia/Jakarta"},
    {"name": "Nairobi", "lat": -1.2921, "lon": 36.8219, "country": "KE", "tz": "Africa/Nairobi"},
    {"name": "Lima", "lat": -12.0464, "lon": -77.0428, "country": "PE", "tz": "America/Lima"},
    {"name": "Auckland", "lat": -36.8485, "lon": 174.7633, "country": "NZ", "tz": "Pacific/Auckland"},
    {"name": "Dublin", "lat": 53.3498, "lon": -6.2603, "country": "IE", "tz": "Europe/Dublin"},
    {"name": "Zurich", "lat": 47.3769, "lon": 8.5417, "country": "CH", "tz": "Europe/Zurich"},
    {"name": "Taipei", "lat": 25.033, "lon": 121.5654, "country": "TW", "tz": "Asia/Taipei"},
    {"name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "country": "BR", "tz": "America/Sao_Paulo"},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473, "country": "ZA", "tz": "Africa/Johannesburg"},
    {"name": "Warsaw", "lat": 52.2297, "lon": 21.0122, "country": "PL", "tz": "Europe/Warsaw"},
    {"name": "Lisbon", "lat": 38.7223, "lon": -9.1393, "country": "PT", "tz": "Europe/Lisbon"},
    {"name": "Oslo", "lat": 59.9139, "lon": 10.7522, "country": "NO", "tz": "Europe/Oslo"},
    {"name": "Helsinki", "lat": 60.1699, "lon": 24.9384, "country": "FI", "tz": "Europe/Helsinki"},
]


class OpenMeteoExtractor:
    """Extracts hourly weather data from the Open-Meteo API."""

    def __init__(self, cities: list[dict] | None = None):
        self.cities = cities or CITIES
        self.extracted_at = datetime.now(timezone.utc).isoformat()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _fetch_city(
        self, client: httpx.AsyncClient, city: dict, days: int = 1
    ) -> list[dict[str, Any]]:
        """Fetch hourly weather for a single city."""
        params = {
            "latitude": city["lat"],
            "longitude": city["lon"],
            "hourly": ",".join(HOURLY_PARAMS),
            "timezone": city.get("tz", "UTC"),
            "forecast_days": days,
        }

        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        records = []
        for i, time_str in enumerate(times):
            record = {
                "city_name": city["name"],
                "latitude": city["lat"],
                "longitude": city["lon"],
                "country": city.get("country", ""),
                "timezone": city.get("tz", "UTC"),
                "observation_time": time_str,
                "extracted_at": self.extracted_at,
            }
            for param in HOURLY_PARAMS:
                values = hourly.get(param, [])
                record[param] = values[i] if i < len(values) else None
            records.append(record)

        logger.info("city_extracted", city=city["name"], records=len(records))
        return records

    async def extract_all(self, days: int = 1) -> list[dict[str, Any]]:
        """Extract weather data for all cities concurrently."""
        all_records: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Batch in groups of 10 to avoid overwhelming the API
            batch_size = 10
            for i in range(0, len(self.cities), batch_size):
                batch = self.cities[i : i + batch_size]
                tasks = [self._fetch_city(client, city, days) for city in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, list):
                        all_records.extend(result)
                    elif isinstance(result, Exception):
                        logger.error("extraction_error", error=str(result))

                if i + batch_size < len(self.cities):
                    await asyncio.sleep(0.5)

        logger.info("extraction_complete", total_records=len(all_records))
        return all_records

    async def extract_historical(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Extract historical weather data using Open-Meteo archive API."""
        archive_url = "https://archive-api.open-meteo.com/v1/archive"
        all_records: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=60) as client:
            for city in self.cities:
                try:
                    resp = await client.get(
                        archive_url,
                        params={
                            "latitude": city["lat"],
                            "longitude": city["lon"],
                            "start_date": start_date,
                            "end_date": end_date,
                            "hourly": ",".join(HOURLY_PARAMS[:10]),
                            "timezone": city.get("tz", "UTC"),
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    hourly = data.get("hourly", {})
                    times = hourly.get("time", [])

                    for i, time_str in enumerate(times):
                        record = {
                            "city_name": city["name"],
                            "latitude": city["lat"],
                            "longitude": city["lon"],
                            "country": city.get("country", ""),
                            "timezone": city.get("tz", "UTC"),
                            "observation_time": time_str,
                            "extracted_at": self.extracted_at,
                        }
                        for param in HOURLY_PARAMS[:10]:
                            values = hourly.get(param, [])
                            record[param] = values[i] if i < len(values) else None
                        all_records.append(record)

                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.error("historical_error", city=city["name"], error=str(e))

        return all_records
