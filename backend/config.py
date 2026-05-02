import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent / ".env")


class Settings(BaseModel):
    app_name: str = "Stocker"
    data_dir: Path = Path(__file__).resolve().parent / "data"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_secret_key: str = os.getenv(
        "SUPABASE_SECRET_KEY",
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )
    supabase_legacy_jwt_secret: str = os.getenv(
        "SUPABASE_LEGACY_JWT_SECRET",
        os.getenv("SUPABASE_JWT_SECRET", ""),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
