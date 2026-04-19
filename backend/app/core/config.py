import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./procera.db")
    upload_storage_path: str = os.getenv("UPLOAD_STORAGE_PATH", "storage")


settings = Settings()
