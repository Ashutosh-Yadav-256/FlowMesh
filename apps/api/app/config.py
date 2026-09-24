from typing import List, Any, Union
import json
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET_PREFIX = "dev-flowmesh-"
_DEV_MASTER_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
_DEV_AGENT_SECRET = "flowmesh-agent-dev-token-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "FlowMesh"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "info"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = ""
    encryption_master_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    allowed_origins: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    allowed_methods: Union[List[str], str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: Union[List[str], str] = ["Authorization", "Content-Type", "X-Tenant-ID", "X-Request-ID"]
    allow_credentials: bool = True

    database_url: str = "sqlite+aiosqlite:///./flowmesh.db"

    nats_url: str = "nats://localhost:4222"
    nats_cluster_id: str = "flowmesh-cluster"

    state_store_provider: str = "memory"
    redis_url: str = "redis://localhost:6379/0"

    agent_enrollment_secret: str = ""

    seed_demo_data: bool = False

    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    rate_limit_auth_per_minute: int = 20

    max_request_body_bytes: int = 1_048_576
    max_json_nesting_depth: int = 10

    search_index_path: str = "./data/search_indexes"
    search_persist_enabled: bool = True

    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        """Validates configuration safety based on environment."""
        is_dev = self.environment in ("development", "test")

        if is_dev:

            if not self.api_secret_key:
                self.api_secret_key = "dev-flowmesh-secret-key-replace-in-production-at-least-32-chars"
            if not self.encryption_master_key:
                self.encryption_master_key = _DEV_MASTER_KEY
            if not self.agent_enrollment_secret:
                self.agent_enrollment_secret = _DEV_AGENT_SECRET

            self.debug = True
            self.seed_demo_data = True
        else:

            if not self.api_secret_key or self.api_secret_key.startswith(_DEV_SECRET_PREFIX):
                raise ValueError(
                    "FATAL: API_SECRET_KEY must be set to a strong, unique secret in non-development environments. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if not self.encryption_master_key or self.encryption_master_key == _DEV_MASTER_KEY:
                raise ValueError(
                    "FATAL: ENCRYPTION_MASTER_KEY must be set to a unique 64-hex-char key in non-development environments. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if not self.agent_enrollment_secret or self.agent_enrollment_secret == _DEV_AGENT_SECRET:
                raise ValueError(
                    "FATAL: AGENT_ENROLLMENT_SECRET must be set in non-development environments."
                )

            if "sqlite" in self.database_url:
                raise ValueError(
                    "FATAL: SQLite is not supported in production. "
                    "Set DATABASE_URL to a PostgreSQL connection string: "
                    "postgresql+asyncpg://user:pass@host:5432/dbname"
                )

            if "*" in self.allowed_origins:
                raise ValueError(
                    "FATAL: Wildcard '*' is not permitted in ALLOWED_ORIGINS in production. "
                    "Specify explicit origins (e.g. https://app.flowmesh.io)."
                )

        return self


settings = Settings()
