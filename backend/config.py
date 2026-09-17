from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # Environment
    HERMES_ENV: str = os.getenv("HERMES_ENV", "development")

    # Security Configuration
    _cors = os.getenv("CORS_ORIGINS", "")
    if _cors:
        CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors.split(",") if origin.strip()]
    elif HERMES_ENV == "production":
        CORS_ORIGINS: List[str] = [
            "http://127.0.0.1:9220",
            "http://localhost:9220",
            "https://web.telegram.org",
        ]
    else:
        CORS_ORIGINS: List[str] = ["*"]

    ALLOW_CREDENTIALS: bool = False if "*" in CORS_ORIGINS else True
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 9220))
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MAX_AGE_SECONDS: int = int(os.getenv("HERMES_TELEGRAM_MAX_AGE_SECONDS", "86400"))
    SESSION_SECRET: str = os.getenv("HERMES_SESSION_SECRET", "hermes-default-dev-secret-key-32bytes!")
    
    # Paths
    BASE_DIR: str = BASE_DIR
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    PROJECTS_DIR: str = os.getenv("HERMES_PROJECTS_DIR", os.path.join(BASE_DIR, "config", "projects"))
    MISSION_DB_PATH: str = os.getenv("HERMES_MISSION_DB_PATH", os.path.join(BASE_DIR, "var", "lib", "missions.db"))
    ORCHESTRATION_DEFAULTS_PATH: str = os.getenv(
        "HERMES_ORCHESTRATION_DEFAULTS_PATH",
        os.path.join(BASE_DIR, "config", "orchestration", "defaults.json")
    )
    
    # Access and Capacity Control
    ALLOW_LOCAL_DEVELOPMENT: bool = os.getenv("HERMES_ALLOW_LOCAL_DEVELOPMENT", "true").lower() == "true"
    _allowlist = os.getenv("HERMES_OPERATOR_ALLOWLIST", "0,123456789")
    OPERATOR_ALLOWLIST: List[int] = [
        int(item.strip()) for item in _allowlist.split(",") if item.strip().isdigit()
    ]
    MAX_ACTIVE_RUNS: int = int(os.getenv("HERMES_MAX_ACTIVE_RUNS", "5"))
    MAX_ACTIVE_AGY_PER_PROJECT: int = int(os.getenv("HERMES_MAX_ACTIVE_AGY_PER_PROJECT", "1"))
    HERMES_ADAPTER_ENABLED: bool = os.getenv("HERMES_HERMES_ADAPTER_ENABLED", "false").lower() == "true"

    @classmethod
    def validate(cls) -> None:
        if cls.MAX_ACTIVE_RUNS < 1:
            raise ValueError(f"MAX_ACTIVE_RUNS must be at least 1, got {cls.MAX_ACTIVE_RUNS}")
        if cls.MAX_ACTIVE_AGY_PER_PROJECT < 1:
            raise ValueError(
                f"MAX_ACTIVE_AGY_PER_PROJECT must be at least 1, got {cls.MAX_ACTIVE_AGY_PER_PROJECT}"
            )
        if cls.HERMES_ENV == "production" and cls.ALLOW_LOCAL_DEVELOPMENT:
            raise ValueError("ALLOW_LOCAL_DEVELOPMENT cannot be True in production")
        if cls.HERMES_ENV == "production" and "*" in cls.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot contain '*' in production")


Config.validate()
config = Config()
