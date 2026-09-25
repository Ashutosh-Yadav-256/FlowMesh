from typing import List, Any, Union
import json
import secrets
import logging
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("flowmesh.config")

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
    allowed_headers: Union[List[str], str] = [
        "Authorization",
        "Content-Type",
        "X-Tenant-ID",
        "X-Request-ID",
        "X-API-Key",
    ]
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
        """Validates configuration safety based on environment and auto-populates secure defaults."""
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
        elif self.environment == "production":
            if not self.api_secret_key or self.api_secret_key.startswith(_DEV_SECRET_PREFIX):
                raise ValueError("SECURITY FAILURE: API_SECRET_KEY must be explicitly set with a persistent secret in production.")

            if not self.encryption_master_key or self.encryption_master_key == _DEV_MASTER_KEY:
                raise ValueError("SECURITY FAILURE: ENCRYPTION_MASTER_KEY must be explicitly configured in production to prevent encrypted credential loss across container restarts.")

            if not self.agent_enrollment_secret or self.agent_enrollment_secret == _DEV_AGENT_SECRET:
                raise ValueError("SECURITY FAILURE: AGENT_ENROLLMENT_SECRET must be explicitly set in production.")

            if "sqlite" in self.database_url:
                logger.warning("Production environment is using SQLite database (%s). PostgreSQL is strongly recommended.", self.database_url)

            if "*" in self.allowed_origins:
                logger.warning("Wildcard '*' in ALLOWED_ORIGINS enabled in production environment.")
        else:
            if not self.api_secret_key or self.api_secret_key.startswith(_DEV_SECRET_PREFIX):
                self.api_secret_key = secrets.token_urlsafe(64)
                logger.warning("API_SECRET_KEY was not set in staging; generated secure random ephemeral key.")

            if not self.encryption_master_key or self.encryption_master_key == _DEV_MASTER_KEY:
                self.encryption_master_key = secrets.token_hex(32)
                logger.warning("ENCRYPTION_MASTER_KEY was not set in staging; generated secure random 256-bit key.")

            if not self.agent_enrollment_secret or self.agent_enrollment_secret == _DEV_AGENT_SECRET:
                self.agent_enrollment_secret = secrets.token_urlsafe(32)
                logger.warning("AGENT_ENROLLMENT_SECRET was not set in staging; generated secure random token.")

        return self


settings = Settings()
