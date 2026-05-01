import { Activity, BadgeDollarSign, Trophy } from "lucide-react";
import { useMemo, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { MetricCard } from "../components/shared/MetricCard";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Badge, Card, DataTableShell, EmptyState, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { money, percent, signedClass } from "../components/shared/format";
import { useRealized } from "../hooks/queries";

type RealizedStockRow = {
  code: string;
  name: string;
  shares: number;
  avg_buy_price: number;
  expense: number;
  income: number;
  realized_pnl: number;
  realized_pnl_rate: number;
};

function formatYAxisK(value: number) {
  if (value === 0) return "0";
  const scaled = value / 1000;
  if (Number.isInteger(scaled)) return `${scaled}k`;
  return `${scaled.toFixed(1)}k`;
}

export function Realized() {
  const { data, isLoading } = useRealized();
  const [sortKey, setSortKey] = useState("realized_pnl");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const stockItems = useMemo<RealizedStockRow[]>(() => {
    const grouped = new Map<string, RealizedStockRow>();

    for (const item of data?.items ?? []) {
      const current = grouped.get(item.code);
      if (current) {
        current.shares += item.shares;
        current.expense += item.cost_basis;
        current.income += item.income;
        current.realized_pnl += item.realized_pnl;
      } else {
        grouped.set(item.code, {
          code: item.code,
          name: item.name,
          shares: item.shares,
          avg_buy_price: 0,
          expense: item.cost_basis,
          income: item.income,
          realized_pnl: item.realized_pnl,
          realized_pnl_rate: 0,
        });
      }
    }

    return Array.from(grouped.values()).map((item) => {
      const avgBuyPrice = item.shares ? item.expense / item.shares : 0;
      const realizedPnlRate = item.expense ? item.realized_pnl / item.expense : 0;

      return {
        ...item,
        avg_buy_price: avgBuyPrice,
        realized_pnl_rate: realizedPnlRate,
      };
    });
  }, [data]);

  const sortedItems = useMemo(() => {
    const getValue = (row: RealizedStockRow, key: string) => {
      if (key === "stock") return `${row.code} ${row.name}`;
      return (row as unknown as Record<string, string | number>)[key] ?? "";
    };

    return sortItems(stockItems, (item) => getValue(item, sortKey), sortDir);
  }, [sortDir, sortKey, stockItems]);

  const summaryRow = useMemo(() => {
    if (!stockItems.length) return null;

    const totalExpense = stockItems.reduce((sum, item) => sum + item.expense, 0);
    const totalIncome = stockItems.reduce((sum, item) => sum + item.income, 0);
    const avgRealizedPnl = stockItems.reduce((sum, item) => sum + item.realized_pnl, 0) / stockItems.length;
    const avgRealizedPnlRate = stockItems.reduce((sum, item) => sum + item.realized_pnl_rate, 0) / stockItems.length;

    return {
      count: stockItems.length,
      totalExpense,
      totalIncome,
      avgRealizedPnl,
      avgRealizedPnlRate,
    };
  }, [stockItems]);

  if (isLoading) return <SkeletonBlock label="載入已實現損益中..." />;
  if (!data) return <EmptyState title="沒有已實現損益資料" />;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="已結束交易"
        title="已實現損益"
        description="回顧已結束交易與股利收入，確認勝率、實現損益與每筆賣出的結果。"
      />

      <div className="metric-grid grid gap-4">
        <MetricCard icon={Trophy} label="勝率" value={data.win_rate * 100} hint="%" description="獲利筆數比例" />
        <MetricCard icon={Activity} label="已實現損益" value={data.total_realized_pnl} hint={percent(data.realized_pnl_rate)} description="已實現損益 ÷ 本金" tone="signed" />
        <MetricCard icon={BadgeDollarSign} label="股利收入" value={data.dividend_income} hint={percent(data.dividend_realized_pnl_rate)} description="股利 ÷ 已實現損益" />
      </div>

      <Card>
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-ink">損益分布</h2>
            <p className="text-sm text-muted">依股票彙總的已實現損益，最多顯示 18 檔。</p>
          </div>
          <Badge tone="neutral">{stockItems.length} 檔</Badge>
        </div>
        {stockItems.length ? (
          <div className="mt-3 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sortedItems.slice(0, 18)} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <XAxis dataKey="code" />
                <YAxis width={56} tickFormatter={formatYAxisK} />
                <Tooltip formatter={(value: number) => [money(value), "已實現損益"]} />
                <Bar dataKey="realized_pnl" name="已實現損益" radius={[6, 6, 0, 0]}>
                  {sortedItems.slice(0, 18).map((entry) => (
                    <Cell key={entry.code} fill={entry.realized_pnl >= 0 ? "#9f1239" : "#047857"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <EmptyState title="尚無已實現交易" description="賣出交易完成後，這裡會顯示依股票彙總的損益分布。" />
        )}
      </Card>

      <div className="grid gap-3 lg:hidden">
        {sortedItems.map((item) => (
          <article key={item.code} className="rounded-2xl border border-line bg-panel p-4 shadow-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-bold">{item.code} {item.name}</div>
                <p className="mt-1 text-sm text-muted">買入均價 {money(item.avg_buy_price)}</p>
              </div>
              <div className={`text-right font-bold ${signedClass(item.realized_pnl)}`}>
                {money(item.realized_pnl)}
                <div className="text-xs">{percent(item.realized_pnl_rate)}</div>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">支出</div>
                <div className="mt-1 font-semibold text-ink">{money(item.expense)}</div>
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">收入</div>
                <div className="mt-1 font-semibold text-ink">{money(item.income)}</div>
              </div>
            </div>
          </article>
        ))}
        {summaryRow ? (
          <article className="rounded-2xl border border-line bg-white/80 p-4 shadow-card">
            <div className="font-bold text-ink">總計</div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">股票</div>
                <div className="mt-1 font-semibold text-ink">{summaryRow.count}</div>
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">支出</div>
                <div className="mt-1 font-semibold text-ink">{money(summaryRow.totalExpense)}</div>
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">收入</div>
                <div className="mt-1 font-semibold text-ink">{money(summaryRow.totalIncome)}</div>
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">已實現損益平均</div>
                <div className={`mt-1 font-semibold ${signedClass(summaryRow.avgRealizedPnl)}`}>{money(summaryRow.avgRealizedPnl)}</div>
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide text-muted">報酬率平均</div>
                <div className={`mt-1 font-semibold ${signedClass(summaryRow.avgRealizedPnlRate)}`}>{percent(summaryRow.avgRealizedPnlRate)}</div>
              </div>
            </div>
          </article>
        ) : null}
      </div>

      <DataTableShell className="hidden lg:block">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="股票" sortKey="stock" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="買入均價" sortKey="avg_buy_price" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="text-right" />
              <SortableHeader label="支出" sortKey="expense" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="text-right" />
              <SortableHeader label="收入" sortKey="income" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="text-right" />
              <SortableHeader label="已實現損益" sortKey="realized_pnl" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="text-right" />
              <SortableHeader label="報酬率" sortKey="realized_pnl_rate" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="text-right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {sortedItems.map((item) => (
              <tr key={item.code} className="bg-panel/70 hover:bg-white/75">
                <td className="px-4 py-3">{item.code} {item.name}</td>
                <td className="px-4 py-3 text-right">{money(item.avg_buy_price)}</td>
                <td className="px-4 py-3 text-right">{money(item.expense)}</td>
                <td className="px-4 py-3 text-right">{money(item.income)}</td>
                <td className={`px-4 py-3 text-right font-semibold ${signedClass(item.realized_pnl)}`}>{money(item.realized_pnl)}</td>
                <td className={`px-4 py-3 text-right ${signedClass(item.realized_pnl_rate)}`}>{percent(item.realized_pnl_rate)}</td>
              </tr>
            ))}
          </tbody>
          {summaryRow ? (
            <tfoot className="border-t border-line bg-white/95 text-[0.7rem] font-bold text-muted">
              <tr>
                <td className="px-4 py-2">{summaryRow.count} 筆</td>
                <td className="px-4 py-2" />
                <td className="px-4 py-2" />
                <td className="px-4 py-2" />
                <td className={`px-4 py-2 text-right ${signedClass(summaryRow.avgRealizedPnl)}`}>{money(summaryRow.avgRealizedPnl)}</td>
                <td className={`px-4 py-2 text-right ${signedClass(summaryRow.avgRealizedPnlRate)}`}>{percent(summaryRow.avgRealizedPnlRate)}</td>
              </tr>
            </tfoot>
          ) : null}
        </table>
      </DataTableShell>
    </section>
  );
}
