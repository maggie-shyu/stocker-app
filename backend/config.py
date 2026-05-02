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
    supabase_jwt_audience: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    supabase_secret_key: str = os.getenv(
        "SUPABASE_SECRET_KEY",
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )
    supabase_legacy_jwt_secret: str = os.getenv(
        "SUPABASE_LEGACY_JWT_SECRET",
        os.getenv("SUPABASE_JWT_SECRET", ""),
    )
    import_max_upload_bytes: int = int(os.getenv("IMPORT_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    import_max_workbook_bytes: int = int(os.getenv("IMPORT_MAX_WORKBOOK_BYTES", str(25 * 1024 * 1024)))
    import_max_rows_per_sheet: int = int(os.getenv("IMPORT_MAX_ROWS_PER_SHEET", "5000"))
    price_lookup_max_codes: int = int(os.getenv("PRICE_LOOKUP_MAX_CODES", "50"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
