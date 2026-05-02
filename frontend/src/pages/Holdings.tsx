import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useMemo, useState } from "react";

import type { Holding } from "../api/types";
import { sortItems } from "../components/shared/sort";
import { Badge, EmptyState, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { money, percent, price, signedClass } from "../components/shared/format";
import { useHoldings } from "../hooks/queries";

const SORT_COLS = [
  { key: "code", label: "代號" },
  { key: "total_shares", label: "股數" },
  { key: "market_value", label: "市值" },
  { key: "unrealized_pnl", label: "損益" },
  { key: "unrealized_pnl_rate", label: "報酬率" },
  { key: "weight", label: "比重" },
] as const;

type SortKey = typeof SORT_COLS[number]["key"];

export function Holdings() {
  const { data, isLoading } = useHoldings();
  const [sortKey, setSortKey] = useState<SortKey>("market_value");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

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

  if (isLoading) return <SkeletonBlock label="載入持股中..." />;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Open positions"
        title="持股狀況"
        description={`${sorted.length} 檔庫存，依成本、現值與未實現損益整理。`}
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

      {sorted.length ? (
        <div className="grid gap-3">
          {sorted.map((holding) => (
            <article key={holding.code} className="rounded-2xl border border-line bg-panel/95 p-4 shadow-card">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-bold">{holding.code} {holding.name}</h2>
                    <Badge tone="accent">{percent(holding.weight)} 配置</Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted">
                    {holding.total_shares.toLocaleString()} 股 · 均價 {price(holding.avg_cost)} · 現價 {price(holding.current_price)}
                  </p>
                </div>
                <div className="sm:text-right">
                  <div className="text-xl font-bold">{money(holding.market_value)}</div>
                  <div className={`text-sm font-semibold ${signedClass(holding.unrealized_pnl)}`}>
                    {money(holding.unrealized_pnl)} · {percent(holding.unrealized_pnl_rate)}
                  </div>
                </div>
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-stone-200">
                <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(Math.max(holding.weight * 100, 4), 100)}%` }} />
              </div>
              <div className="mt-4 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                {holding.lots.map((lot) => (
                  <div key={`${holding.code}-${lot.date}-${lot.cost_per_share}`} className="rounded-xl border border-line/70 bg-white/75 px-3 py-2 text-sm text-muted">
                    <span className="font-semibold text-ink">{lot.date}</span> · {lot.shares.toLocaleString()} 股 · 成本 {money(lot.cost_basis)}
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="尚無持股" description="新增買進交易後，庫存批次與未實現損益會出現在這裡。" />
      )}
    </section>
  );
}
