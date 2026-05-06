import { ArrowDown, ArrowUp, ArrowUpDown, ChevronDown } from "lucide-react";
import { useMemo, useState } from "react";

import type { Holding } from "./types";
import { money, percent, price, signedClass } from "../../shared/lib/format";
import { Badge, EmptyState, PageHeader, SkeletonBlock } from "../../shared/ui/UI";
import { sortItems } from "../ledger/lib/sort";
import { useApiQuery, queryKeys } from "../../platform/api/query";

const SORT_COLS = [
  { key: "code", label: "代號" },
  { key: "total_shares", label: "股數" },
  { key: "market_value", label: "市值" },
  { key: "cumulative_pnl", label: "損益" },
  { key: "cumulative_pnl_rate", label: "報酬率" },
] as const;

type SortKey = typeof SORT_COLS[number]["key"];

function LotTable({ holding }: { holding: Holding }) {
  if (!holding.lots.length) return <p className="px-1 text-sm text-muted">沒有批次資料。</p>;

  return (
    <div className="space-y-1.5">
      <div className="grid grid-cols-3 gap-2 px-1 text-xs font-bold uppercase tracking-[0.12em] text-muted">
        <span>日期</span>
        <span className="text-right">股數</span>
        <span className="text-right">買價</span>
      </div>
      {holding.lots.map((lot) => (
        <div
          key={`${holding.code}-${lot.date}-${lot.cost_per_share}`}
          className="grid grid-cols-3 gap-2 rounded-xl border border-line/70 bg-white/75 px-3 py-2.5 text-sm"
        >
          <span className="font-semibold text-ink">{lot.date}</span>
          <span className="text-right text-muted">{lot.shares.toLocaleString()} 股</span>
          <span className="text-right text-muted">{price(lot.cost_per_share)}</span>
        </div>
      ))}
    </div>
  );
}

function useHoldings() {
  return useApiQuery<Holding[]>(queryKeys.holdings, "/holdings");
}

export function HoldingsPage() {
  const { data, isLoading } = useHoldings();
  const [sortKey, setSortKey] = useState<SortKey>("market_value");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [expandedCode, setExpandedCode] = useState<string | null>(null);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sorted = useMemo(() => {
    const items = data ?? [];
    return sortItems(items, (item: Holding) => item[sortKey], sortDir);
  }, [data, sortKey, sortDir]);

  const filtered = useMemo(() => {
    // Filter out holdings that are purely from day trades (當沖)
    return sorted.filter((holding) => {
      // Check if all lots are from day trades
      const allDayTrade = holding.lots.every((lot) => lot.trade_type === "當沖");
      // Only filter out if ALL lots are day trades AND total shares is 0 or very small
      // (This shouldn't normally happen since holdings exclude fully sold positions)
      return !allDayTrade || holding.total_shares > 1e-9;
    });
  }, [sorted]);

  if (isLoading) return <SkeletonBlock label="載入持股中..." />;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Open positions"
        title="持股狀況"
        description={`${filtered.length} 檔庫存，整理成本、現值與未實現損益(預扣賣出費用)。`}
      />

      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-line bg-panel/90 p-3 text-sm shadow-card">
        <span className="px-1 font-semibold text-muted">排序</span>
        {SORT_COLS.map((col) => {
          const active = col.key === sortKey;
          return (
            <button
              key={col.key}
              type="button"
              onClick={() => handleSort(col.key)}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 font-semibold transition ${
                active ? "bg-teal-50 text-accent" : "text-muted hover:bg-white/80 hover:text-ink"
              }`}
            >
              {col.label}
              {active
                ? sortDir === "asc"
                  ? <ArrowUp className="h-3 w-3" />
                  : <ArrowDown className="h-3 w-3" />
                : <ArrowUpDown className="h-3 w-3 opacity-40" />}
            </button>
          );
        })}
      </div>

      {filtered.length ? (
        <div className="grid gap-3">
          {filtered.map((holding) => {
            const isExpanded = expandedCode === holding.code;
            return (
              <article
                key={holding.code}
                className="rounded-2xl border border-line bg-panel/95 shadow-card transition"
              >
                {/* Clickable header */}
                <button
                  type="button"
                  className="w-full cursor-pointer p-4 text-left"
                  onClick={() => setExpandedCode(isExpanded ? null : holding.code)}
                  aria-expanded={isExpanded}
                  aria-label={`${isExpanded ? "收合" : "展開"} ${holding.code} ${holding.name} 的批次明細`}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-lg font-bold">{holding.code} {holding.name}</h2>
                        <Badge tone="accent">{percent(holding.weight)} 配置</Badge>
                      </div>
                      <p className="mt-2 text-sm text-muted">
                        {holding.total_shares.toLocaleString()} 股 · 成本均 {price(holding.net_avg_cost)} · 買均 {price(holding.avg_cost)} · 現價 {price(holding.current_price)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 sm:justify-end">
                      <div className="sm:text-right">
                        <div className="text-xl font-bold">{money(holding.market_value)}</div>
                        <div className={`text-sm font-semibold ${signedClass(holding.cumulative_pnl)}`}>
                          {money(holding.cumulative_pnl)} · {percent(holding.cumulative_pnl_rate)}
                        </div>
                      </div>
                      <ChevronDown
                        className={`h-5 w-5 shrink-0 text-muted transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                      />
                    </div>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-stone-200">
                    <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(Math.max(holding.weight * 100, 4), 100)}%` }} />
                  </div>
                </button>

                {/* Expandable lot details */}
                {isExpanded && (
                  <div className="border-t border-line/60 px-4 pb-4 pt-3">
                    <LotTable holding={holding} />
                  </div>
                )}
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState title="尚無持股" description="新增買進交易後，庫存批次與未實現損益會出現在這裡。" />
      )}
    </section>
  );
}
