I'll analyze your current backend architecture to assess whether it can handle continuous intraday price polling without compromising the portfolio ledger. Let me explore the codebase.

Analyze current architecture

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/api/dashboard.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/domain/ledger/interfaces.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/domain/portfolio/price_service.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/api/stocks.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/api/holdings.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/infrastructure/market_data/yfinance_quote_provider.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/domain/portfolio/read_module.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/api/deps.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/infrastructure/supabase/ledger_store.py#1-1), lines 1 to 150

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/models/domain/ledger.py)

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/models/domain/portfolio.py)

Searched for regex `router|@router` (`**/backend/api/*.py`), 20 results

Read [](file:///Users/meimei/workspace/ntu/repo/stocker/backend/domain/portfolio/calculator.py#1-1), lines 1 to 100

Based on the architectural analysis, **yes, your backend can handle continuous intraday price polling without compromising ledger stability** — but with some caveats and optimization opportunities.

## ✅ **Current Strengths**

1. **Hard separation between ledger writes and price reads**

   - Ledger (source of truth) is only touched by transaction/cashflow CRUD
   - Price polling is completely independent, cached with 60s TTL
   - Async non-blocking I/O prevents yfinance latency from blocking ledger operations
2. **Stateless portfolio calculations**

   - read_module.py fetches latest ledger + latest prices, computes in-memory
   - No stored aggregations to keep synchronized during continuous polling
   - Ledger integrity unaffected by price volatility
3. **Graceful degradation**

   - Missing/delayed prices return `delayed=True` flag, dashboard still renders with stale prices
   - Won't cascade failures to ledger operations

## ⚠️ **Stability Risks at Scale**

1. **Shared singleton PriceService**

   - Single 60s TTL cache shared across all concurrent users
   - High concurrent intraday polling → cache thrashing or lock contention if multiple requests overlap
   - **Risk:** Tail latency spikes during market open when many users refresh simultaneously
2. **Unbounded ledger I/O per read operation**

   - Every portfolio read triggers fresh Supabase query for all transactions
   - With many users polling prices every 5-10 seconds, ledger DB becomes read-heavy
   - **Risk:** Cascading slowdown if Supabase connection pool exhausts
3. **No rate limiting or circuit breaker**

   - Continuous polling could abuse yfinance API limits (returns 429 silently, degrades gracefully but burns quota)
   - YfinanceQuoteProvider has retry logic but no backoff strategy
4. **Price cache keyed only by ticker, not user**

   - If 100 users hold the same stock, all share one cache entry
   - Good for memory, but all 100 concurrent requests wait on same 60s window

## 📋 **Recommendations for Production Intraday Polling**

| Priority         | Issue                     | Solution                                                                                                         |
| ---------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **High**   | Ledger read contention    | Add Redis cache for `(user_id, timestamp_bucket)` → aggregated portfolio; invalidate on transaction CRUD only |
| **High**   | PriceService bottleneck   | Implement per-user cache with staggered refresh (don't all refresh at 60s boundary)                              |
| **Medium** | Yfinance quota exhaustion | Add circuit breaker + exponential backoff; track 429 responses                                                   |
| **Medium** | Supabase connection pool  | Monitor pool exhaustion; add connection pooling layer (pgBouncer)                                                |
| **Low**    | Stale price cascade       | Add explicit TTL to frontend cache to prevent request storms                                                     |

Would you like me to assess **how significant the ledger contention risk is** with your current expected user load, or dive into implementing one of the above mitigations?
