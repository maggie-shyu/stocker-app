from __future__ import annotations

from datetime import date
from typing import Any

from backend.models.schemas import (
    UserSettings,
    CashflowCreate,
    CashflowRecord,
    StockLookup,
    TransactionCreate,
    TransactionRecord,
)
from backend.services.calculator import calculate_trade_financials


class SupabaseService:
    def __init__(self, client: Any, user_id: str):
        self._db = client
        self._user_id = user_id
        self._stock_cache: list[StockLookup] | None = None

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        return default if value is None else float(value)

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        return None if value is None else float(value)

    def _build_tx_record(
        self,
        row: dict[str, Any],
        settings: UserSettings,
        *,
        current_price: float = 0.0,
    ) -> TransactionRecord:
        action = row["action"]
        buy_shares = self._optional_float(row.get("buy_shares"))
        buy_price = self._optional_float(row.get("buy_price"))
        sell_shares = self._optional_float(row.get("sell_shares"))
        sell_price = self._optional_float(row.get("sell_price"))
        dividend_income = self._optional_float(row.get("dividend_income"))

        if action == "買":
            shares, price = buy_shares, buy_price
        elif action == "賣":
            shares, price = sell_shares, sell_price
        else:
            shares, price = None, None

        financials = calculate_trade_financials(
            action=action,
            trade_type=row.get("trade_type") or "一般",
            code=row["code"],
            shares=shares,
            price=price,
            amount=dividend_income if action == "股利" else None,
            current_price=current_price,
            settings=settings,
        )
        return TransactionRecord(
            id=str(row["id"]),
            date=date.fromisoformat(str(row["date"])[:10]),
            action=action,
            code=row["code"],
            name=row["name"],
            trade_type=row.get("trade_type") or "一般",
            buy_shares=buy_shares,
            buy_price=buy_price,
            sell_shares=sell_shares,
            sell_price=sell_price,
            current_price=financials.current_price,
            raw_fee=financials.raw_fee,
            discounted_fee=financials.discounted_fee,
            tax=financials.tax,
            amount=financials.amount,
            trade_cost=financials.trade_cost,
            expense=financials.expense,
            income=financials.income,
            reason=row.get("reason"),
            discount_rate=financials.discount_rate,
        )

    def read_transactions(self) -> list[TransactionRecord]:
        rows = (
            self._db.table("transactions")
            .select("*")
            .eq("user_id", self._user_id)
            .order("date")
            .execute()
            .data
        )
        settings = self.get_settings()
        return [self._build_tx_record(row, settings) for row in rows]

    def append_transaction(
        self,
        payload: TransactionCreate,
        *,
        current_price: float = 0.0,
    ) -> TransactionRecord:
        row = {
            "user_id": self._user_id,
            "date": str(payload.date),
            "action": payload.action,
            "code": payload.code,
            "name": payload.name,
            "trade_type": payload.trade_type,
            "buy_shares": payload.buy_shares,
            "buy_price": payload.buy_price,
            "sell_shares": payload.sell_shares,
            "sell_price": payload.sell_price,
            "dividend_income": payload.dividend_income,
            "reason": payload.reason,
        }
        data = self._db.table("transactions").insert(row).execute().data[0]
        return self._build_tx_record(data, self.get_settings(), current_price=current_price)

    def replace_transactions(self, payloads: list[TransactionCreate]) -> int:
        (
            self._db.table("transactions")
            .delete()
            .eq("user_id", self._user_id)
            .execute()
        )
        if not payloads:
            return 0
        rows = [
            {
                "user_id": self._user_id,
                "date": str(payload.date),
                "action": payload.action,
                "code": payload.code,
                "name": payload.name,
                "trade_type": payload.trade_type,
                "buy_shares": payload.buy_shares,
                "buy_price": payload.buy_price,
                "sell_shares": payload.sell_shares,
                "sell_price": payload.sell_price,
                "dividend_income": payload.dividend_income,
                "reason": payload.reason,
            }
            for payload in payloads
        ]
        self._db.table("transactions").insert(rows).execute()
        return len(rows)

    def update_transaction(self, tx_id: str, payload: TransactionCreate) -> TransactionRecord:
        row = {
            "date": str(payload.date),
            "action": payload.action,
            "code": payload.code,
            "name": payload.name,
            "trade_type": payload.trade_type,
            "buy_shares": payload.buy_shares,
            "buy_price": payload.buy_price,
            "sell_shares": payload.sell_shares,
            "sell_price": payload.sell_price,
            "dividend_income": payload.dividend_income,
            "reason": payload.reason,
        }
        result = (
            self._db.table("transactions")
            .update(row)
            .eq("id", tx_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(tx_id)
        return self._build_tx_record(result.data[0], self.get_settings())

    def delete_transaction(self, tx_id: str) -> None:
        result = (
            self._db.table("transactions")
            .delete()
            .eq("id", tx_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(tx_id)

    def read_cashflows(self) -> list[CashflowRecord]:
        rows = (
            self._db.table("cashflow")
            .select("*")
            .eq("user_id", self._user_id)
            .order("date")
            .execute()
            .data
        )
        records: list[CashflowRecord] = []
        for row in rows:
            records.append(
                CashflowRecord(
                    id=str(row["id"]),
                    date=date.fromisoformat(str(row["date"])[:10]),
                    deposit=self._float(row.get("deposit")),
                    withdrawal=self._float(row.get("withdrawal")),
                )
            )
        return records

    def append_cashflow(self, payload: CashflowCreate) -> CashflowRecord:
        data = (
            self._db.table("cashflow")
            .insert(
                {
                    "user_id": self._user_id,
                    "date": str(payload.date),
                    "deposit": payload.deposit,
                    "withdrawal": payload.withdrawal,
                }
            )
            .execute()
            .data[0]
        )
        return CashflowRecord(
            id=str(data["id"]),
            date=payload.date,
            deposit=payload.deposit,
            withdrawal=payload.withdrawal,
        )

    def replace_cashflows(self, payloads: list[CashflowCreate]) -> int:
        (
            self._db.table("cashflow")
            .delete()
            .eq("user_id", self._user_id)
            .execute()
        )
        if not payloads:
            return 0
        rows = [
            {
                "user_id": self._user_id,
                "date": str(payload.date),
                "deposit": payload.deposit,
                "withdrawal": payload.withdrawal,
            }
            for payload in payloads
        ]
        self._db.table("cashflow").insert(rows).execute()
        return len(rows)

    def update_cashflow(self, cf_id: str, payload: CashflowCreate) -> CashflowRecord:
        result = (
            self._db.table("cashflow")
            .update(
                {
                    "date": str(payload.date),
                    "deposit": payload.deposit,
                    "withdrawal": payload.withdrawal,
                }
            )
            .eq("id", cf_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(cf_id)
        for cashflow in self.read_cashflows():
            if cashflow.id == cf_id:
                return cashflow
        raise KeyError(cf_id)

    def delete_cashflow(self, cf_id: str) -> None:
        result = (
            self._db.table("cashflow")
            .delete()
            .eq("id", cf_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(cf_id)

    def get_settings(self) -> UserSettings:
        result = (
            self._db.table("user_settings")
            .select(
                "commission_discount_rate,base_commission_rate,minimum_fee,"
                "odd_lot_minimum_fee,stock_tax_rate,day_trade_tax_rate,"
                "etf_tax_rate,bond_etf_tax_rate"
            )
            .eq("user_id", self._user_id)
            .maybe_single()
            .execute()
        )
        if result.data is None:
            return UserSettings(commission_discount_rate=1.0)
        return UserSettings(**result.data)

    def update_settings(self, settings: UserSettings) -> UserSettings:
        data = settings.model_dump()
        data["user_id"] = self._user_id
        self._db.table("user_settings").upsert(data).execute()
        return settings

    def read_stocks(self) -> list[StockLookup]:
        if self._stock_cache is not None:
            return self._stock_cache
        rows = self._db.table("stocks").select("code, name").execute().data
        self._stock_cache = [
            StockLookup(code=row["code"], name=row["name"])
            for row in rows
        ]
        return self._stock_cache

    def search_stocks(self, query: str, *, limit: int = 20) -> list[StockLookup]:
        query = query.strip().lower()
        all_stocks = self.read_stocks()
        if not query:
            return all_stocks[:limit]

        def score(stock: StockLookup) -> tuple[int, str]:
            code = stock.code.lower()
            name = stock.name.lower()
            if code == query or name == query:
                return (0, code)
            if code.startswith(query) or name.startswith(query):
                return (1, code)
            return (2, code)

        matches = [
            stock
            for stock in all_stocks
            if query in stock.code.lower() or query in stock.name.lower()
        ]
        return sorted(matches, key=score)[:limit]
