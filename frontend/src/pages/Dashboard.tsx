import { Activity, BadgeDollarSign, Banknote, Landmark, LineChart, TrendingUp, Wallet } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { MetricCard } from "../components/shared/MetricCard";
import { Badge, Card, EmptyState, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { money, percent, signedClass } from "../components/shared/format";
import { useDashboard } from "../hooks/queries";

const colors = ["#0f766e", "#314c38", "#b45309", "#2563eb", "#9f1239", "#047857", "#57534e"];

export function Dashboard() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) return <SkeletonBlock label="載入儀表板資料中..." />;
  if (error || !data) {
    return <EmptyState title="儀表板資料暫時無法載入" description="請稍後重新整理，或確認後端服務是否正在執行。" />;
  }

  const priceTone = data.price_status.delayed > 0 ? "warn" : "good";
  const priceLabel =
    data.price_status.total === 0
      ? "尚無持股報價"
      : `${data.price_status.priced}/${data.price_status.total} 檔已有報價`;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="投資總覽"
        title="投資儀表板"
        description="用一眼能讀懂的方式追蹤帳戶淨值、損益、現金與庫存配置。"
        action={<Badge tone={priceTone}>{priceLabel}</Badge>}
      />

      <Card className="overflow-hidden bg-gradient-to-br from-moss to-[#10251e] p-0 text-white">
        <div className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[1.3fr_0.7fr] lg:p-7">
          <div>
            <p className="text-sm font-semibold text-white/70">帳戶淨值</p>
            <div className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">{money(data.account_value)}</div>
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <span className="rounded-full bg-white/12 px-3 py-1.5">本金 {money(data.principal)}</span>
              <span className="rounded-full bg-white/12 px-3 py-1.5">股票市值 {money(data.stock_market_value)}</span>
              <span className="rounded-full bg-white/12 px-3 py-1.5">現金 {money(data.cash_balance)}</span>
            </div>
          </div>
          <div className="rounded-3xl border border-white/15 bg-white/10 p-4">
            <p className="text-sm font-semibold text-white/70">帳戶損益</p>
            <div className={`mt-3 text-3xl font-bold ${data.account_pnl >= 0 ? "text-rose-100" : "text-emerald-100"}`}>
              {money(data.account_pnl)}
            </div>
            <p className="mt-2 text-sm text-white/70">相對本金 {percent(data.account_pnl_rate)}</p>
          </div>
        </div>
      </Card>

      <div className="metric-grid grid gap-4">
        <MetricCard icon={Wallet} label="帳戶淨值" value={data.account_value} description="市值 + 現金" />
        <MetricCard icon={Landmark} label="股票市值" value={data.stock_market_value} description="依可用報價計算" />
        <MetricCard icon={Banknote} label="現金部位" value={data.cash_balance} description="本金與交易後餘額" />
        <MetricCard icon={TrendingUp} label="帳戶損益" value={data.account_pnl} hint={percent(data.account_pnl_rate)} tone="signed" />
        <MetricCard icon={LineChart} label="未實現損益" value={data.unrealized_pnl} hint={percent(data.unrealized_pnl_rate)} tone="signed" />
        <MetricCard icon={Activity} label="已實現損益" value={data.realized_pnl} hint={percent(data.realized_pnl_rate)} tone="signed" />
        <MetricCard
          icon={BadgeDollarSign}
          label="年化報酬率"
          value={data.annualized_return_rate}
          valueFormatter={percent}
          description={`依 ${data.investment_years.toFixed(2)} 年換算`}
          tone="signed"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-ink">持股配置</h2>
              <p className="text-sm text-muted">依目前市值排序，最多顯示前六檔。</p>
            </div>
          </div>
          {data.holdings_pie.length ? (
            <>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={data.holdings_pie} dataKey="market_value" nameKey="name" innerRadius={66} outerRadius={106} paddingAngle={2}>
                      {data.holdings_pie.map((entry, index) => (
                        <Cell key={entry.name} fill={colors[index % colors.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [money(value), "市值"]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {data.holdings_pie.slice(0, 6).map((item, index) => (
                  <div key={item.name} className="flex items-center justify-between rounded-xl bg-white/75 px-3 py-2 text-sm">
                    <span className="flex min-w-0 items-center gap-2">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: colors[index % colors.length] }} />
                      <span className="truncate">{item.name}</span>
                    </span>
                    <span className="font-semibold">{percent(item.weight)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <EmptyState title="尚無持股配置" description="新增買進交易後，這裡會顯示庫存市值比例。" />
          )}
        </Card>

        <Card>
          <div>
            <h2 className="text-lg font-bold text-ink">最近交易</h2>
            <p className="text-sm text-muted">快速確認最新寫入的買賣與股利。</p>
          </div>
          <div className="mt-4 space-y-3">
            {data.recent_transactions.length ? data.recent_transactions.map((tx) => (
              <article key={tx.id} className="rounded-2xl border border-line/70 bg-white/80 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={tx.action === "買" ? "accent" : tx.action === "賣" ? "warn" : "good"}>{tx.action}</Badge>
                      <span className="font-bold text-ink">{tx.code} {tx.name}</span>
                    </div>
                    <p className="mt-2 text-xs text-muted">{tx.date} · {tx.trade_type}</p>
                  </div>
                  <div className={`text-right font-bold ${signedClass(tx.income - tx.expense)}`}>
                    {money(tx.income || tx.expense)}
                  </div>
                </div>
              </article>
            )) : (
              <EmptyState title="尚無交易紀錄" description="新增第一筆交易後，這裡會顯示最近三筆。" />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
