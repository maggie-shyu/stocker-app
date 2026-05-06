from unittest.mock import MagicMock

from backend.infrastructure.supabase.stock_catalog import SupabaseStockCatalog


def test_read_stocks_caches_first_result():
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = [
        {"code": "0050", "name": "元大台灣50"},
        {"code": "2330", "name": "台積電"},
    ]
    catalog = SupabaseStockCatalog(client)

    first = catalog.read_stocks()
    second = catalog.read_stocks()

    assert [stock.code for stock in first] == ["0050", "2330"]
    assert [stock.name for stock in second] == ["元大台灣50", "台積電"]
    client.table.assert_called_once_with("stocks")


def test_search_stocks_prioritizes_exact_then_prefix_then_contains():
    client = MagicMock()
    catalog = SupabaseStockCatalog(client)
    catalog._stock_cache = [
        type("Stock", (), {"code": "0050", "name": "元大台灣50"})(),
        type("Stock", (), {"code": "0056", "name": "元大高股息"})(),
        type("Stock", (), {"code": "1101", "name": "台泥"})(),
        type("Stock", (), {"code": "5000", "name": "測試005"})(),
    ]

    results = catalog.search_stocks("005", limit=3)

    assert [stock.code for stock in results] == ["0050", "0056", "5000"]


def test_search_stocks_returns_limited_head_when_query_blank():
    client = MagicMock()
    catalog = SupabaseStockCatalog(client)
    catalog._stock_cache = [
        type("Stock", (), {"code": "0050", "name": "元大台灣50"})(),
        type("Stock", (), {"code": "0056", "name": "元大高股息"})(),
        type("Stock", (), {"code": "2330", "name": "台積電"})(),
    ]

    results = catalog.search_stocks("   ", limit=2)

    assert [stock.code for stock in results] == ["0050", "0056"]
