import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent / ".env")


def _parse_csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    if not value.strip():
        return []
    return [item.strip().lower() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str
    data_dir: Path
    cors_origins: list[str]
    supabase_url: str
    supabase_jwt_audience: str
    supabase_secret_key: str
    supabase_legacy_jwt_secret: str
    import_max_upload_bytes: int
    import_max_workbook_bytes: int
    import_max_rows_per_sheet: int
    price_lookup_max_codes: int
    admin_email_allowlist: list[str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name="Stocker",
        data_dir=Path(__file__).resolve().parent / "data",
        cors_origins=_parse_csv_env("CORS_ORIGINS") or ["http://localhost:5173", "http://127.0.0.1:5173"],
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated"),
        supabase_secret_key=os.getenv("SUPABASE_SECRET_KEY", os.getenv("SUPABASE_SERVICE_KEY", "")),
        supabase_legacy_jwt_secret=os.getenv("SUPABASE_LEGACY_JWT_SECRET", os.getenv("SUPABASE_JWT_SECRET", "")),
        import_max_upload_bytes=int(os.getenv("IMPORT_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
        import_max_workbook_bytes=int(os.getenv("IMPORT_MAX_WORKBOOK_BYTES", str(25 * 1024 * 1024))),
        import_max_rows_per_sheet=int(os.getenv("IMPORT_MAX_ROWS_PER_SHEET", "5000")),
        price_lookup_max_codes=int(os.getenv("PRICE_LOOKUP_MAX_CODES", "50")),
        admin_email_allowlist=_parse_csv_env("ADMIN_EMAIL_ALLOWLIST"),
    )
