from typing import Any

from pydantic import BaseModel, Field


class CurrentUserCapabilities(BaseModel):
    is_admin: bool


class AdminOverview(BaseModel):
    total_users: int
    users_with_transactions: int
    users_with_cashflows: int
    supabase_memory_usage_percent: float | None = None
    cpu_busy_percent: float | None = None
    disk_usage_percent: float | None = None
    connection_rate_percent: float | None = None
    active_queries: int | None = None


class AdminTableSummary(BaseModel):
    name: str
    label: str
    description: str
    row_count: int


class AdminTablePage(BaseModel):
    table_name: str
    label: str
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total: int = Field(ge=0)
    columns: list[str]
    items: list[dict[str, Any]]
