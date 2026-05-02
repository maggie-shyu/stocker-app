"""One-time script: migrates existing CSV data to Supabase for the first user."""

import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
USER_EMAIL = os.environ["MIGRATE_USER_EMAIL"]
USER_PASSWORD = os.environ["MIGRATE_USER_PASSWORD"]

DATA_DIR = Path(__file__).parent.parent / "backend" / "data"

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
auth = client.auth.sign_in_with_password({"email": USER_EMAIL, "password": USER_PASSWORD})
user_id = auth.user.id
print(f"Migrating data for user {user_id}")


def _float_or_none(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


with open(DATA_DIR / "transactions.csv", newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))

tx_records = [
    {
        "user_id": user_id,
        "date": row["date"],
        "action": row["action"],
        "code": row["code"],
        "name": row["name"],
        "trade_type": row.get("trade_type") or "一般",
        "buy_shares": _float_or_none(row.get("buy_shares", "")),
        "buy_price": _float_or_none(row.get("buy_price", "")),
        "sell_shares": _float_or_none(row.get("sell_shares", "")),
        "sell_price": _float_or_none(row.get("sell_price", "")),
        "dividend_income": _float_or_none(row.get("dividend_income", "")),
        "reason": row.get("reason") or None,
    }
    for row in rows
]
client.table("transactions").insert(tx_records).execute()
print(f"Migrated {len(tx_records)} transactions")

with open(DATA_DIR / "cashflow.csv", newline="", encoding="utf-8") as fh:
    cashflow_rows = list(csv.DictReader(fh))

cashflow_records = [
    {
        "user_id": user_id,
        "date": row["date"],
        "deposit": float(row.get("deposit") or 0),
        "withdrawal": float(row.get("withdrawal") or 0),
        "is_principal": str(row.get("is_principal", "")).lower() in ("true", "1", "yes"),
    }
    for row in cashflow_rows
]
client.table("cashflow").insert(cashflow_records).execute()
print(f"Migrated {len(cashflow_records)} cashflow rows")

with open(DATA_DIR / "stocks.csv", newline="", encoding="utf-8") as fh:
    stock_rows = list(csv.DictReader(fh))

stock_records = [
    {"code": row["code"].strip(), "name": row["name"].strip()}
    for row in stock_rows
    if row.get("code") and row.get("name")
]
client.table("stocks").upsert(stock_records).execute()
print(f"Migrated {len(stock_records)} stocks")

with open(DATA_DIR / "settings.json", encoding="utf-8") as fh:
    settings_data = json.load(fh)

client.table("user_settings").upsert(
    {
        "user_id": user_id,
        "commission_discount_rate": settings_data.get("commission_discount_rate", 1.0),
    }
).execute()
print("Migrated settings")
print("Migration complete.")
