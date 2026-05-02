import { Activity, BadgeDollarSign, Coins, Trophy } from "lucide-react";
import { useMemo, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { MetricCard } from "../components/shared/MetricCard";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Button, Card, EmptyState, PageHeader, SkeletonBlock, Badge } from "../components/shared/UI";
import { money, percent, price, signedClass } from "../components/shared/format";
import { useRealized } from "../hooks/queries";
import { useQuery } from "@tanstack/react-query";

type RealizedStockRow = {
  code: string;
  name: string;
  shares: number;
  avg_sell_price: number;
  avg_buy_price: number;
  capital_gain: number;
  dividend_income: number;
  realized_profit: number;
  realized_pnl_rate: number;
  isDividendOnly: boolean;
  dividendYield: number | null;
  twseDividendYield: number | null;
};

function formatYAxisK(value: number) {
  if (value === 0) return "0";
  const scaled = value / 1000;
  if (Number.isInteger(scaled)) return `${scaled}k`;
  return `${scaled.toFixed(1)}k`;
}

export function Realized() {
  const { data, isLoading } = useRealized();
  const [sortKey, setSortKey] = useState("realized_profit");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Fetch TWSE dividend yield for all listed stocks (cached 1h)
  const { data: twseData } = useQuery<Record<string, number>>({
    queryKey: ["twse-dividend-yield"],
    staleTime: 60 * 60 * 1000,
    queryFn: async () => {
      const res = await fetch("https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d");
      const json: { Code: string; DividendYield: string }[] = await res.json();
      const map: Record<string, number> = {};
      for (const item of json) {
        const val = parseFloat(item.DividendYield);
        if (!isNaN(val)) map[item.Code] = val;
      }
      return map;
    },
  });

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
    setPage(1);
  };

  const stockItems = useMemo<RealizedStockRow[]>(() => {
    const grouped = new Map<string, RealizedStockRow>();

    for (const item of data?.items ?? []) {
      const current = grouped.get(item.code);
      if (current) {
        current.shares += item.shares;
        current.avg_sell_price += item.avg_sell_price * item.shares;
        current.avg_buy_price += item.avg_buy_price * item.shares;
        current.capital_gain += item.realized_pnl;
      } else {
        grouped.set(item.code, {
          code: item.code,
          name: item.name,
          shares: item.shares,
          avg_sell_price: item.avg_sell_price * item.shares,
          avg_buy_price: item.avg_buy_price * item.shares,
          capital_gain: item.realized_pnl,
          dividend_income: 0,
          realized_profit: 0,
          realized_pnl_rate: 0,
          isDividendOnly: false,
          dividendYield: null,
          twseDividendYield: null,
        });
      }
    }

    for (const item of data?.dividend_by_stock ?? []) {
      const current = grouped.get(item.code);
      if (current) {
        current.dividend_income += item.dividend_income;
      } else {
        grouped.set(item.code, {
          code: item.code,
          name: item.name,
          shares: 0,
          avg_sell_price: 0,
          avg_buy_price: 0,
          capital_gain: 0,
          dividend_income: item.dividend_income,
          realized_profit: item.dividend_income,
          realized_pnl_rate: 0,
          isDividendOnly: true,
          dividendYield: null,
          twseDividendYield: null,
        });
      }
    }

    return Array.from(grouped.values()).map((item) => {
      const avgSellPrice = item.shares ? item.avg_sell_price / item.shares : 0;
      const avgBuyPrice = item.shares ? item.avg_buy_price / item.shares : 0;
      const realizedProfit = item.capital_gain + item.dividend_income;
      const realizedPnlRate = item.avg_buy_price ? realizedProfit / item.avg_buy_price : 0;
      // 殖利率 = 股息 / 買進總成本 (僅當有買進成本時才計算)
      const dividendYield = item.isDividendOnly
        ? null
        : item.avg_buy_price > 0
          ? item.dividend_income / item.avg_buy_price
          : null;
      const twseDividendYield = twseData?.[item.code] ?? null;

      return {
        ...item,
        avg_sell_price: avgSellPrice,
        avg_buy_price: avgBuyPrice,
        realized_profit: realizedProfit,
        realized_pnl_rate: realizedPnlRate,
        dividendYield,
        twseDividendYield,
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

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page]);

  const summaryRow = useMemo(() => {
    if (!stockItems.length) return null;

    const totalCapitalGain = stockItems.reduce((sum, item) => sum + item.capital_gain, 0);
    const totalDividendIncome = stockItems.reduce((sum, item) => sum + item.dividend_income, 0);
    const avgRealizedPnl = stockItems.reduce((sum, item) => sum + item.realized_profit, 0) / stockItems.length;
    const avgRealizedPnlRate = stockItems.reduce((sum, item) => sum + item.realized_pnl_rate, 0) / stockItems.length;

    return {
      count: stockItems.length,
      totalCapitalGain,
      totalDividendIncome,
      totalRealizedProfit: totalCapitalGain + totalDividendIncome,
      avgRealizedPnl,
      avgRealizedPnlRate,
    };
  }, [stockItems]);

  if (isLoading) return <SkeletonBlock label="載入已實現損益中..." />;
  if (!data) return <EmptyState title="沒有已實現損益資料" />;
  const capitalGainRate = data.total_realized_pnl ? ((summaryRow?.totalCapitalGain ?? 0) / data.total_realized_pnl) : 0;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="已結束交易"
        title="已實現損益"
        description="回顧已結束交易與股利收入，確認勝率、實現損益與每筆賣出的結果。"
      />

      <div className="metric-grid grid gap-4">
        <MetricCard icon={Trophy} label="勝率" value={data.win_rate * 100} hint="%" description="獲利筆數比例" />
        <MetricCard icon={Activity} label="已實現收益" value={data.total_realized_pnl} hint={percent(data.realized_pnl_rate)} description="(資本利得 + 股利) ÷ 本金" tone="signed" />
        <MetricCard icon={Coins} label="資本利得" value={summaryRow?.totalCapitalGain ?? 0} hint={percent(capitalGainRate)} description="資本利得 ÷ 已實現損益" tone="signed" />
        <MetricCard icon={BadgeDollarSign} label="股利收入" value={data.dividend_income} hint={percent(data.dividend_realized_pnl_rate)} description="股利 ÷ 已實現損益" tone="signed" />
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
                <Tooltip formatter={(value: number) => [money(value), "已實現收益"]} />
                <Bar dataKey="realized_profit" name="已實現收益" radius={[6, 6, 0, 0]}>
                  {sortedItems.slice(0, 18).map((entry) => (
                    <Cell key={entry.code} fill={entry.realized_profit >= 0 ? "#9f1239" : "#047857"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <EmptyState title="尚無已實現交易" description="賣出交易完成後，這裡會顯示依股票彙總的損益分布。" />
        )}
      </Card>

      <div className="rounded-2xl border border-line bg-white/75">
        <div className="border-b border-line px-4 py-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="font-semibold text-ink">損益明細</h3>
              <p className="mt-1 text-sm text-muted">
                {sortedItems.length <= 0 ? "顯示 0 筆" : `顯示 ${(page - 1) * pageSize + 1} - ${Math.min(page * pageSize, sortedItems.length)} 筆`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1"
                max={Math.ceil(sortedItems.length / pageSize) || 1}
                value={page}
                onChange={(e) => setPage(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-12 rounded-lg border border-line bg-white px-2 py-2 text-center text-sm font-semibold text-ink"
                title="跳轉至特定頁"
              />
              <span className="text-sm font-semibold text-muted">/ {Math.ceil(sortedItems.length / pageSize) || 1}</span>
            </div>
          </div>
        </div>

        <div className="grid gap-3 p-4 lg:hidden">
          {paginatedItems.map((item) => (
            <article key={item.code} className="rounded-2xl border border-line bg-panel p-4 shadow-card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-bold">{item.code} {item.name}</div>
                  <p className="mt-1 text-sm text-muted">賣均 {price(item.avg_sell_price)} · 買均 {price(item.avg_buy_price)}</p>
                </div>
                <div className={`text-right font-bold ${signedClass(item.realized_profit)}`}>
                  {money(item.realized_profit)}
                  <div className="text-xs">{percent(item.realized_pnl_rate)}</div>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-muted">資本利得</div>
                  <div className={`mt-1 font-semibold ${signedClass(item.capital_gain)}`}>{money(item.capital_gain)}</div>
                </div>
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-muted">股息收入</div>
                  <div className={`mt-1 font-semibold ${signedClass(item.dividend_income)}`}>{money(item.dividend_income)}</div>
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="relative z-0 hidden overflow-x-auto overflow-y-visible lg:block">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="股票" sortKey="stock" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="賣均" sortKey="avg_sell_price" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="買均" sortKey="avg_buy_price" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="資本利得" sortKey="capital_gain" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="股息收入" sortKey="dividend_income" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="已實現收益" sortKey="realized_profit" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {paginatedItems.map((item) => (
              <tr key={item.code} className="bg-panel/70 hover:bg-white/75">
                <td className="px-4 py-3">{item.code} {item.name}</td>
                <td className="px-4 py-3 text-right">{price(item.avg_sell_price)}</td>
                <td className="px-4 py-3 text-right">{price(item.avg_buy_price)}</td>
                <td className={`px-4 py-3 text-right ${signedClass(item.capital_gain)}`}>{money(item.capital_gain)}</td>
                <td className={`px-4 py-3 text-right ${signedClass(item.dividend_income)}`}>{money(item.dividend_income)}</td>
                <td className={`px-4 py-3 text-right font-semibold ${signedClass(item.realized_profit)}`}>
                  <div>{money(item.realized_profit)}</div>
                  {item.capital_gain !== 0 ? (
                    <div className="mt-1 text-xs font-normal text-muted">{percent(item.realized_pnl_rate)}</div>
                  ) : (
                    <div className="mt-1 text-xs font-normal text-muted">-</div>
                  )}
                </td>
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
                <td className="px-4 py-2" />
                <td className={`px-4 py-2 text-right ${signedClass(summaryRow.totalRealizedProfit)}`}>{money(summaryRow.totalRealizedProfit)}</td>
              </tr>
            </tfoot>
          ) : null}
        </table>
        </div>
      </div>
    </section>
  );
}
