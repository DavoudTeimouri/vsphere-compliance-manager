from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "production"
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "postgresql://vcm:***@localhost:5432/vcm_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    REDIS_URL: str = "redis://localhost:***@admin2024!"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "VCM@admin2024!"
    ADMIN_EMAIL: str = "admin@example.com"

    # LDAP
    LDAP_ENABLED: bool = False
    LDAP_SERVER_URL: str = ""
    LDAP_BASE_DN: str = ""
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""
    LDAP_USER_FILTER: str = "(sAMAccountName={username})"
    LDAP_GROUP_ADMIN: str = ""
    LDAP_GROUP_OPERATOR: str = ""
    LDAP_USE_SSL: bool = False
    LDAP_TIMEOUT: int = 10

    # Analysis
    ANALYSIS_SCHEDULE_CRON: str = "0 2 * * *"
    ANALYSIS_TIMEOUT_SECONDS: int = 3600
    ANALYSIS_MAX_WORKERS: int = 4

    UPLOAD_PATH: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
