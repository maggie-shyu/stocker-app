from functools import lru_cache

from config import get_settings
from services.csv_service import CsvService
from services.price_service import PriceService


@lru_cache
def get_csv_service() -> CsvService:
    return CsvService(get_settings().data_dir)


@lru_cache
def get_price_service() -> PriceService:
    return PriceService()
