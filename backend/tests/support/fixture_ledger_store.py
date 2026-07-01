from __future__ import annotations

import csv
import json
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from backend.domain.portfolio.calculator import calculate_trade_financials
from backend.models.api.ledger import CashflowCreate, FeedbackCreate, TransactionCreate
from backend.models.domain.ledger import CashflowRecord, FeedbackRecord, TransactionRecord, UserSettings
from backend.models.domain.portfolio import StockLookup


class FixtureLedgerStore:
    _write_lock = threading.Lock()
    _transaction_fields = [
        "date",
        "action",
        "code",
        "name",
        "trade_type",
        "buy_shares",
        "buy_price",
        "sell_shares",
        "sell_price",
        "dividend_shares",
        "dividend_price",
        "reason",
    ]

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self._stock_cache: list[StockLookup] | None = None
        self._feedbacks: list[FeedbackRecord] = [
            FeedbackRecord(
                id="feedback-1",
                subject="儀表板資訊",
                body="希望儀表板可以多一點現金部位資訊",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ]

    @staticmethod
    def _float(value: str, default: float = 0.0) -> float:
        if value is None or str(value).strip() == "":
            return default
        return float(value)

    @staticmethod
    def _optional_float(value: str) -> float | None:
        if value is None or str(value).strip() == "":
            return None
        return float(value)

    @staticmethod
    def _normalize_trade_inputs(
        action: str,
        *,
        buy_shares: float | None = None,
        buy_price: float | None = None,
        sell_shares: float | None = None,
        sell_price: float | None = None,
        dividend_shares: float | None = None,
        dividend_price: float | None = None,
    ) -> tuple[float | None, float | None]:
        if action == "買":
            return buy_shares, buy_price
        if action == "賣":
            return sell_shares, sell_price
        if dividend_shares is not None and dividend_price is not None:
            return dividend_shares, dividend_price
        return None, None

    def _build_transaction_record(
        self,
        *,
        row_id: int,
        tx_date: date,
        action: str,
        code: str,
        name: str,
        trade_type: str,
        buy_shares: float | None,
        buy_price: float | None,
        sell_shares: float | None,
        sell_price: float | None,
        dividend_shares: float | None,
        dividend_price: float | None,
        reason: str | None,
        current_price: float = 0,
    ) -> TransactionRecord:
        settings = self.get_settings()
        shares, price = self._normalize_trade_inputs(
            action,
            buy_shares=buy_shares,
            buy_price=buy_price,
            sell_shares=sell_shares,
            sell_price=sell_price,
            dividend_shares=dividend_shares,
            dividend_price=dividend_price,
        )
        financials = calculate_trade_financials(
            action=action,
            trade_type=trade_type,
            code=code,
            shares=shares,
            price=price,
            current_price=current_price,
            settings=settings,
        )
        return TransactionRecord(
            id=str(row_id),
            date=tx_date,
            action=action,
            code=code,
            name=name,
            trade_type=trade_type,
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
            reason=reason,
            discount_rate=financials.discount_rate,
        )

    @classmethod
    def _transaction_row_from_payload(cls, payload: TransactionCreate) -> dict[str, str | float]:
        return {
            "date": str(payload.date),
            "action": payload.action,
            "code": payload.code,
            "name": payload.name,
            "trade_type": payload.trade_type,
            "buy_shares": payload.buy_shares if payload.buy_shares is not None else "",
            "buy_price": payload.buy_price if payload.buy_price is not None else "",
            "sell_shares": payload.sell_shares if payload.sell_shares is not None else "",
            "sell_price": payload.sell_price if payload.sell_price is not None else "",
            "dividend_shares": payload.dividend_shares if payload.dividend_shares is not None else "",
            "dividend_price": payload.dividend_price if payload.dividend_price is not None else "",
            "reason": payload.reason or "",
        }

    def _read_csv_rows(self, filename: str) -> tuple[list[str], list[dict[str, str]]]:
        path = self.data_dir / filename
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            return list(reader.fieldnames or []), list(reader)

    def _write_csv_rows(self, filename: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        path = self.data_dir / filename
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def read_transactions(self) -> list[TransactionRecord]:
        path = self.data_dir / "transactions.csv"
        records: list[TransactionRecord] = []
        with open(path, newline="", encoding="utf-8") as fh:
            for row_id, row in enumerate(csv.DictReader(fh), start=1):
                action = row["action"]
                buy_shares = self._optional_float(row["buy_shares"])
                buy_price = self._optional_float(row["buy_price"])
                sell_shares = self._optional_float(row["sell_shares"])
                sell_price = self._optional_float(row["sell_price"])
                dividend_shares = self._optional_float(row.get("dividend_shares"))
                dividend_price = self._optional_float(row.get("dividend_price"))
                records.append(
                    self._build_transaction_record(
                        row_id=row_id,
                        tx_date=date.fromisoformat(row["date"]),
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
                        reason=row.get("reason") or None,
                    )
                )
        return records

    def append_transaction(
        self,
        payload: TransactionCreate,
        *,
        current_price: float = 0,
    ) -> TransactionRecord:
        with self._write_lock:
            _, rows = self._read_csv_rows("transactions.csv")
            row_id = len(rows) + 1
            rows.append(self._transaction_row_from_payload(payload))
            self._write_csv_rows("transactions.csv", self._transaction_fields, rows)

        return self._build_transaction_record(
            row_id=row_id,
            tx_date=payload.date,
            action=payload.action,
            code=payload.code,
            name=payload.name,
            trade_type=payload.trade_type,
            buy_shares=payload.buy_shares,
            buy_price=payload.buy_price,
            sell_shares=payload.sell_shares,
            sell_price=payload.sell_price,
            dividend_shares=payload.dividend_shares,
            dividend_price=payload.dividend_price,
            reason=payload.reason,
            current_price=current_price,
        )

    def update_transaction(
        self,
        row_id: int | str,
        payload: TransactionCreate,
    ) -> TransactionRecord:
        row_index = int(row_id)
        with self._write_lock:
            _, rows = self._read_csv_rows("transactions.csv")
            if row_index < 1 or row_index > len(rows):
                raise KeyError(row_id)
            rows[row_index - 1] = self._transaction_row_from_payload(payload)
            self._write_csv_rows("transactions.csv", self._transaction_fields, rows)

        return self._build_transaction_record(
            row_id=row_index,
            tx_date=payload.date,
            action=payload.action,
            code=payload.code,
            name=payload.name,
            trade_type=payload.trade_type,
            buy_shares=payload.buy_shares,
            buy_price=payload.buy_price,
            sell_shares=payload.sell_shares,
            sell_price=payload.sell_price,
            dividend_shares=payload.dividend_shares,
            dividend_price=payload.dividend_price,
            reason=payload.reason,
        )

    def delete_transaction(self, row_id: int | str) -> None:
        row_index = int(row_id)
        with self._write_lock:
            fieldnames, rows = self._read_csv_rows("transactions.csv")
            if row_index < 1 or row_index > len(rows):
                raise KeyError(row_id)
            rows.pop(row_index - 1)
            self._write_csv_rows("transactions.csv", fieldnames, rows)

    def read_cashflows(self) -> list[CashflowRecord]:
        path = self.data_dir / "cashflow.csv"
        records: list[CashflowRecord] = []
        with open(path, newline="", encoding="utf-8") as fh:
            for row_id, row in enumerate(csv.DictReader(fh), start=1):
                records.append(
                    CashflowRecord(
                        id=str(row_id),
                        date=date.fromisoformat(row["date"]),
                        deposit=self._float(row.get("deposit", "")),
                        withdrawal=self._float(row.get("withdrawal", "")),
                    )
                )
        return records

    def append_cashflow(self, payload: CashflowCreate) -> CashflowRecord:
        path = self.data_dir / "cashflow.csv"
        with self._write_lock:
            current = self.read_cashflows()

            row_id = len(current) + 1
            with open(path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    payload.date,
                    payload.deposit if payload.deposit else "",
                    payload.withdrawal if payload.withdrawal else "",
                ])

        return CashflowRecord(
            id=row_id,
            date=payload.date,
            deposit=payload.deposit,
            withdrawal=payload.withdrawal,
        )

    def update_cashflow(self, row_id: int | str, payload: CashflowCreate) -> CashflowRecord:
        row_index = int(row_id)
        with self._write_lock:
            fieldnames, rows = self._read_csv_rows("cashflow.csv")
            if row_index < 1 or row_index > len(rows):
                raise KeyError(row_id)
            rows[row_index - 1] = {
                "date": str(payload.date),
                "deposit": payload.deposit if payload.deposit else "",
                "withdrawal": payload.withdrawal if payload.withdrawal else "",
            }
            self._write_csv_rows("cashflow.csv", fieldnames, rows)

        return self.read_cashflows()[row_index - 1]

    def delete_cashflow(self, row_id: int | str) -> None:
        row_index = int(row_id)
        with self._write_lock:
            fieldnames, rows = self._read_csv_rows("cashflow.csv")
            if row_index < 1 or row_index > len(rows):
                raise KeyError(row_id)
            rows.pop(row_index - 1)
            self._write_csv_rows("cashflow.csv", fieldnames, rows)

    def read_feedbacks(self) -> list[FeedbackRecord]:
        return list(self._feedbacks)

    def append_feedback(self, payload: FeedbackCreate) -> FeedbackRecord:
        now = datetime.now(timezone.utc)
        record = FeedbackRecord(
            id=f"feedback-{len(self._feedbacks) + 1}",
            subject=payload.subject,
            body=payload.body,
            created_at=now,
            updated_at=now,
        )
        self._feedbacks.insert(0, record)
        return record

    def update_feedback(self, feedback_id: str, payload: FeedbackCreate) -> FeedbackRecord:
        for index, feedback in enumerate(self._feedbacks):
            if feedback.id == feedback_id:
                updated = feedback.model_copy(
                    update={
                        "subject": payload.subject,
                        "body": payload.body,
                        "updated_at": datetime.now(timezone.utc),
                    }
                )
                self._feedbacks[index] = updated
                return updated
        raise KeyError(feedback_id)

    def delete_feedback(self, feedback_id: str) -> None:
        for index, feedback in enumerate(self._feedbacks):
            if feedback.id == feedback_id:
                self._feedbacks.pop(index)
                return
        raise KeyError(feedback_id)

    def get_settings(self) -> UserSettings:
        path = self.data_dir / "settings.json"
        with open(path, encoding="utf-8") as fh:
            return UserSettings(**json.load(fh))

    def read_stocks(self) -> list[StockLookup]:
        if self._stock_cache is not None:
            return self._stock_cache
        path = self.data_dir / "stocks.csv"
        stocks: list[StockLookup] = []
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                code = row.get("code", "").strip()
                name = row.get("name", "").strip()
                if code and name:
                    stocks.append(StockLookup(code=code, name=name))
        self._stock_cache = stocks
        return stocks

    def upsert_stock(self, code: str, name: str) -> None:
        stocks = self.read_stocks()
        self._stock_cache = [
            stock for stock in stocks if stock.code != code
        ] + [StockLookup(code=code, name=name)]

    def search_stocks(self, query: str, *, limit: int = 20) -> list[StockLookup]:
        query = query.strip().lower()
        if not query:
            return self.read_stocks()[:limit]

        def score(stock: StockLookup) -> tuple[int, str]:
            code = stock.code.lower()
            name = stock.name.lower()
            if code == query or name == query:
                return (0, code)
            if code.startswith(query) or name.startswith(query):
                return (1, code)
            return (2, code)

        matches = [
            stock for stock in self.read_stocks()
            if query in stock.code.lower() or query in stock.name.lower()
        ]
        return sorted(matches, key=score)[:limit]
