import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "OpsLab Task API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./opslab.db")
    otel_traces_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "")


settings = Settings()
