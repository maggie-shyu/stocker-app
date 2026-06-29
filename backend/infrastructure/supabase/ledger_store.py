from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from postgrest.exceptions import APIError

from backend.domain.portfolio.calculator import calculate_trade_financials
from backend.models.api.ledger import CashflowCreate, FeedbackCreate, TransactionCreate
from backend.models.domain.ledger import CashflowRecord, FeedbackRecord, TransactionRecord, UserSettings


class SupabaseLedgerStore:
    _settings_columns = (
        "commission_discount_rate,base_commission_rate,minimum_fee,"
        "odd_lot_minimum_fee,cash_dividend_transfer_fee,"
        "stock_tax_rate,day_trade_tax_rate,"
        "etf_tax_rate,bond_etf_tax_rate"
    )
    _legacy_settings_columns = (
        "commission_discount_rate,base_commission_rate,minimum_fee,"
        "odd_lot_minimum_fee,stock_tax_rate,day_trade_tax_rate,"
        "etf_tax_rate,bond_etf_tax_rate"
    )

    def __init__(self, client: Any, user_id: str):
        self._db = client
        self._user_id = user_id

    @staticmethod
    def _is_missing_column_error(error: APIError) -> bool:
        return getattr(error, "code", None) == "42703"

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        return default if value is None else float(value)

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def _optional_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    def _build_feedback_record(self, row: dict[str, Any]) -> FeedbackRecord:
        return FeedbackRecord(
            id=str(row["id"]),
            subject=str(row["subject"]),
            body=str(row.get("body") or ""),
            created_at=self._optional_datetime(row.get("created_at")),
            updated_at=self._optional_datetime(row.get("updated_at")),
        )

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
        dividend_shares = self._optional_float(row.get("dividend_shares"))
        dividend_price = self._optional_float(row.get("dividend_price"))
        dividend_income = self._optional_float(row.get("dividend_income"))

        if action == "買":
            shares, price = buy_shares, buy_price
        elif action == "賣":
            shares, price = sell_shares, sell_price
        elif dividend_shares is not None and dividend_price is not None:
            shares, price = dividend_shares, dividend_price
        else:
            shares, price = None, None

        dividend_amount = None if action == "股利" and shares is not None and price is not None else dividend_income
        financials = calculate_trade_financials(
            action=action,
            trade_type=row.get("trade_type") or "一般",
            code=row["code"],
            shares=shares,
            price=price,
            amount=dividend_amount if action == "股利" else None,
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
            dividend_shares=dividend_shares,
            dividend_price=dividend_price,
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

    def _resolve_settings(self, settings: UserSettings | None) -> UserSettings:
        return settings if settings is not None else self.get_settings()

    def read_transactions(self, settings: UserSettings | None = None) -> list[TransactionRecord]:
        resolved_settings = self._resolve_settings(settings)
        rows = (
            self._db.table("transactions")
            .select("*")
            .eq("user_id", self._user_id)
            .order("date")
            .execute()
            .data
        )
        return [self._build_tx_record(row, resolved_settings) for row in rows]

    def append_transaction(
        self,
        payload: TransactionCreate,
        settings: UserSettings | None = None,
        *,
        current_price: float = 0.0,
    ) -> TransactionRecord:
        resolved_settings = self._resolve_settings(settings)
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
            "dividend_shares": payload.dividend_shares,
            "dividend_price": payload.dividend_price,
            "dividend_income": payload.dividend_income,
            "reason": payload.reason,
        }
        data = self._db.table("transactions").insert(row).execute().data[0]
        return self._build_tx_record(data, resolved_settings, current_price=current_price)

    def replace_transactions(self, payloads: list[TransactionCreate]) -> int:
        self._db.table("transactions").delete().eq("user_id", self._user_id).execute()
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
                "dividend_shares": payload.dividend_shares,
                "dividend_price": payload.dividend_price,
                "dividend_income": payload.dividend_income,
                "reason": payload.reason,
            }
            for payload in payloads
        ]
        self._db.table("transactions").insert(rows).execute()
        return len(rows)

    def update_transaction(
        self,
        tx_id: str,
        payload: TransactionCreate,
        settings: UserSettings | None = None,
    ) -> TransactionRecord:
        resolved_settings = self._resolve_settings(settings)
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
            "dividend_shares": payload.dividend_shares,
            "dividend_price": payload.dividend_price,
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
        return self._build_tx_record(result.data[0], resolved_settings)

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
        return [
            CashflowRecord(
                id=str(row["id"]),
                date=date.fromisoformat(str(row["date"])[:10]),
                deposit=self._float(row.get("deposit")),
                withdrawal=self._float(row.get("withdrawal")),
            )
            for row in rows
        ]

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
        self._db.table("cashflow").delete().eq("user_id", self._user_id).execute()
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
        row = result.data[0]
        row_date = row.get("date")
        return CashflowRecord(
            id=str(row["id"]),
            date=date.fromisoformat(str(row_date)[:10]) if row_date is not None else payload.date,
            deposit=self._float(row.get("deposit"), float(payload.deposit)),
            withdrawal=self._float(row.get("withdrawal"), float(payload.withdrawal)),
        )

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

    def read_feedbacks(self) -> list[FeedbackRecord]:
        rows = (
            self._db.table("feedbacks")
            .select("*")
            .eq("user_id", self._user_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )
        return [self._build_feedback_record(row) for row in rows]

    def append_feedback(self, payload: FeedbackCreate) -> FeedbackRecord:
        data = (
            self._db.table("feedbacks")
            .insert({"user_id": self._user_id, "subject": payload.subject, "body": payload.body})
            .execute()
            .data[0]
        )
        return self._build_feedback_record(data)

    def update_feedback(self, feedback_id: str, payload: FeedbackCreate) -> FeedbackRecord:
        result = (
            self._db.table("feedbacks")
            .update({"subject": payload.subject, "body": payload.body, "updated_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", feedback_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(feedback_id)
        return self._build_feedback_record(result.data[0])

    def delete_feedback(self, feedback_id: str) -> None:
        result = (
            self._db.table("feedbacks")
            .delete()
            .eq("id", feedback_id)
            .eq("user_id", self._user_id)
            .execute()
        )
        if not result.data:
            raise KeyError(feedback_id)

    def get_settings(self) -> UserSettings:
        try:
            result = (
                self._db.table("user_settings")
                .select(self._settings_columns)
                .eq("user_id", self._user_id)
                .maybe_single()
                .execute()
            )
        except APIError as error:
            if not self._is_missing_column_error(error):
                raise
            result = (
                self._db.table("user_settings")
                .select(self._legacy_settings_columns)
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
        try:
            self._db.table("user_settings").upsert(data).execute()
        except APIError as error:
            if not self._is_missing_column_error(error):
                raise
            legacy_data = {key: value for key, value in data.items() if key != "cash_dividend_transfer_fee"}
            self._db.table("user_settings").upsert(legacy_data).execute()
        return settings
