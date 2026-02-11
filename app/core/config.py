from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings using Pydantic Settings.
    Loads from environment variables and optionally from a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENV: str

    # Database Settings
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_SERVER: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str = "1433"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True

    # AWS Settings
    AWS_S3_BUCKET: str
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"

    # API Settings
    PROJECT_NAME: str = "Python Tools Server"
# Singleton instance
settings = Settings()
