"""Core configuration and settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application
    app_name: str = "websearch-api"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "websearch_api"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Search Providers
    google_api_key: str = ""
    google_search_engine_id: str = ""
    bing_api_key: str = ""

    # OAuth - Okta
    okta_domain: str = ""
    okta_client_id: str = ""
    okta_client_secret: str = ""

    # OAuth - Microsoft Entra ID
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_client_secret: str = ""

    # API Security
    api_key_header: str = "X-API-Key"
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # OpenTelemetry
    otel_service_name: str = "websearch-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Search Configuration
    search_cache_ttl_seconds: int = 3600
    search_max_results: int = 100
    search_default_results: int = 10
    search_timeout_seconds: int = 10


settings = Settings()
