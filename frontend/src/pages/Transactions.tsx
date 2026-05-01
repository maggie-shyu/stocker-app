import { Copy, Pencil, Plus, Trash2, Wand2 } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { portfolioQueryKeys, useInvalidateQueries } from "../api/query";
import type { Transaction } from "../api/types";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Badge, Button, Card, DataTableShell, EmptyState, Field, PageHeader, SelectField, SkeletonBlock } from "../components/shared/UI";
import { money } from "../components/shared/format";
import { useTransactions } from "../hooks/queries";

const EMPTY_FORM = {
  date: new Date().toISOString().slice(0, 10),
  action: "買",
  code: "",
  name: "",
  trade_type: "一般",
  shares: "",
  price: "",
  dividend_income: "",
  reason: "",
};

function txToForm(tx: Transaction) {
  return {
    date: tx.date,
    action: tx.action,
    code: tx.code,
    name: tx.name,
    trade_type: tx.trade_type,
    shares: String(tx.buy_shares ?? tx.sell_shares ?? ""),
    price: String(tx.buy_price ?? tx.sell_price ?? ""),
    dividend_income: tx.action === "股利" ? String(tx.amount) : "",
    reason: tx.reason ?? "",
  };
}

function signedTradeAmount(tx: Transaction) {
  return tx.action === "買" ? -tx.amount : tx.amount;
}

function signedMoney(value: number) {
  if (value > 0) return `+${money(value)}`;
  if (value < 0) return `-${money(Math.abs(value))}`;
  return money(value);
}

function signedAmountClass(value: number) {
  if (value > 0) return "text-gain";
  if (value < 0) return "text-loss";
  return "text-muted";
}

const INPUT =
  "min-h-11 w-full rounded-xl border border-line bg-white/85 px-3 py-2 text-sm text-ink shadow-sm transition placeholder:text-stone-400 focus:border-accent focus:bg-white focus:ring-2 focus:ring-accent/15";

export function Transactions() {
  const { data, isLoading } = useTransactions();
  const invalidateQueries = useInvalidateQueries();

  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [sortKey, setSortKey] = useState("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sortedItems = useMemo(() => {
    const items = data?.items ?? [];
    return sortItems(items, (tx) => {
      if (sortKey === "shares") return tx.buy_shares ?? tx.sell_shares ?? 0;
      if (sortKey === "amount") return signedTradeAmount(tx);
      return (tx as unknown as Record<string, string | number>)[sortKey] ?? "";
    }, sortDir);
  }, [data, sortKey, sortDir]);

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    return {
      count: items.length,
      amount: items.reduce((sum, tx) => sum + signedTradeAmount(tx), 0),
    };
  }, [data]);

  const [suggestions, setSuggestions] = useState<{ code: string; name: string }[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const comboboxRef = useRef<HTMLDivElement>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (comboboxRef.current && !comboboxRef.current.contains(e.target as Node)) setShowSuggestions(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const fetchSuggestions = useCallback((query: string) => {
    clearTimeout(searchTimer.current);
    if (!query.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      const res = await api.get<{ code: string; name: string }[]>("/stocks/search", { params: { q: query } });
      setSuggestions(res.data);
      setShowSuggestions(res.data.length > 0);
    }, 200);
  }, []);

  const handleNameChange = (value: string) => {
    setForm((f) => ({ ...f, name: value }));
    fetchSuggestions(value);
  };

  const handleCodeChange = useCallback(async (value: string) => {
    setForm((f) => ({ ...f, code: value }));
    if (!value.trim()) return;
    const res = await api.get<{ code: string; name: string }[]>("/stocks/search", { params: { q: value } });
    const exact = res.data.find((s) => s.code === value);
    if (exact) setForm((f) => ({ ...f, name: exact.name }));
  }, []);

  const selectStock = (stock: { code: string; name: string }) => {
    setForm((f) => ({ ...f, code: stock.code, name: stock.name }));
    setShowSuggestions(false);
  };

  const amount = useMemo(() => {
    if (form.action === "股利") return Number(form.dividend_income || 0);
    return Number(form.shares || 0) * Number(form.price || 0);
  }, [form.action, form.dividend_income, form.price, form.shares]);

  const preview = useQuery({
    queryKey: ["fee-preview", form.action, form.trade_type, amount],
    enabled: amount > 0,
    queryFn: async () =>
      (await api.get("/stocks/preview-fee", { params: { action: form.action, trade_type: form.trade_type, amount } })).data,
  });

  const invalidateAll = () => {
    return invalidateQueries(portfolioQueryKeys);
  };

  const buildPayload = () => {
    const shares = Number(form.shares || 0);
    const price = Number(form.price || 0);
    return {
      date: form.date,
      action: form.action,
      code: form.code,
      name: form.name,
      trade_type: form.trade_type,
      buy_shares: form.action === "買" ? shares : undefined,
      buy_price: form.action === "買" ? price : undefined,
      sell_shares: form.action === "賣" ? shares : undefined,
      sell_price: form.action === "賣" ? price : undefined,
      dividend_income: form.action === "股利" ? Number(form.dividend_income || 0) : undefined,
      reason: form.reason,
    };
  };

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, date: new Date().toISOString().slice(0, 10) });
    setEditingId(null);
  };

  const createMutation = useMutation({
    mutationFn: () => api.post("/transactions", buildPayload()),
    onSuccess: () => {
      setForm((f) => ({ ...f, code: "", name: "", shares: "", price: "", dividend_income: "", reason: "" }));
      invalidateAll();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (id: number) => api.put(`/transactions/${id}`, buildPayload()),
    onSuccess: () => {
      resetForm();
      invalidateAll();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/${id}`),
    onSuccess: invalidateAll,
  });

  const handleEdit = (tx: Transaction) => {
    setEditingId(tx.id);
    setForm(txToForm(tx));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDuplicate = (tx: Transaction) => {
    setEditingId(null);
    setForm({ ...txToForm(tx), date: new Date().toISOString().slice(0, 10) });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = (tx: Transaction) => {
    if (window.confirm(`確定要刪除 ${tx.date} ${tx.action} ${tx.name}？`)) deleteMutation.mutate(tx.id);
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (editingId !== null) updateMutation.mutate(editingId);
    else createMutation.mutate();
  };

  if (isLoading) return <SkeletonBlock label="載入交易紀錄中..." />;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Trade ledger"
        title="交易紀錄"
        description={
          <>
            共 {data?.total ?? 0} 筆交易
            {editingId !== null ? <span className="ml-2 font-semibold text-accent">正在編輯 #{editingId}</span> : null}
          </>
        }
      />

      <Card>
        <form id="transaction-form" onSubmit={submit} className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              {["買", "賣", "股利"].map((action) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => setForm({ ...form, action })}
                  className={`rounded-full border px-4 py-2 text-sm font-bold transition ${
                    form.action === action ? "border-accent bg-teal-50 text-accent" : "border-line bg-white/75 text-muted hover:text-ink"
                  }`}
                >
                  {action}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              {editingId !== null ? <Button type="button" tone="secondary" onClick={resetForm}>取消</Button> : null}
              <Button>
                <Plus className="h-4 w-4" aria-hidden="true" />
                {editingId !== null ? "更新" : "新增"}
              </Button>
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-6">
            <Field label="日期" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            <Field label="代號" placeholder="代號" value={form.code} onChange={(e) => handleCodeChange(e.target.value)} required />
            <div ref={comboboxRef} className="relative space-y-1.5">
              <span className="text-xs font-bold uppercase tracking-[0.14em] text-muted">股票名稱</span>
              <input
                className={INPUT}
                placeholder="股票"
                value={form.name}
                onChange={(e) => handleNameChange(e.target.value)}
                onFocus={() => form.name && setShowSuggestions(suggestions.length > 0)}
                required
              />
              {showSuggestions ? (
                <ul className="absolute left-0 top-full z-20 mt-1 max-h-52 w-64 overflow-y-auto rounded-xl border border-line bg-white shadow-lg">
                  {suggestions.map((s) => (
                    <li
                      key={s.code}
                      onMouseDown={() => selectStock(s)}
                      className="cursor-pointer px-3 py-2 text-sm hover:bg-teal-50"
                    >
                      <span className="font-mono text-muted">{s.code}</span>
                      <span className="ml-2">{s.name}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            <SelectField label="市場規則" value={form.trade_type} onChange={(e) => setForm({ ...form, trade_type: e.target.value })}>
              <option value="一般">一般</option>
              <option value="當沖">當沖</option>
            </SelectField>
            {form.action === "股利" ? (
              <Field label="股利收入" placeholder="股利收入" value={form.dividend_income} onChange={(e) => setForm({ ...form, dividend_income: e.target.value })} required />
            ) : (
              <>
                <Field label="股數" placeholder="股數" value={form.shares} onChange={(e) => setForm({ ...form, shares: e.target.value })} required />
                <Field label="價格" placeholder="價格" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
              </>
            )}
          </div>

          <div className="grid gap-3 lg:grid-cols-[1fr_18rem]">
            <Field label="決策原因" placeholder="決策原因" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
            <div className="rounded-2xl border border-line bg-white/75 p-3 text-sm">
              <div className="flex items-center gap-2 font-bold text-ink">
                <Wand2 className="h-4 w-4 text-accent" aria-hidden="true" />
                費用預估
              </div>
              <p className="mt-2 text-muted">
                手續費 {money(preview.data?.discounted_fee ?? 0)} · 支出 {money(preview.data?.expense ?? 0)}
              </p>
            </div>
          </div>
        </form>
      </Card>

      <div className="grid gap-3 lg:hidden">
        {sortedItems.length ? sortedItems.map((tx) => (
          <article key={tx.id} className={`rounded-2xl border bg-panel p-4 shadow-card ${editingId === tx.id ? "border-accent" : "border-line"}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={tx.action === "買" ? "accent" : tx.action === "賣" ? "warn" : "good"}>{tx.action}</Badge>
                  <span className="font-bold">{tx.code} {tx.name}</span>
                </div>
                <p className="mt-2 text-sm text-muted">{tx.date} · {tx.buy_shares ?? tx.sell_shares ?? "-"} 股</p>
                {tx.reason ? <p className="mt-2 line-clamp-2 text-sm text-muted">{tx.reason}</p> : null}
              </div>
              <div className="text-right font-bold">{money(tx.amount)}</div>
            </div>
            <div className="mt-3 flex justify-end gap-1">
              <Button type="button" tone="ghost" title="編輯" onClick={() => handleEdit(tx)}><Pencil className="h-4 w-4" /></Button>
              <Button type="button" tone="ghost" title="複製" onClick={() => handleDuplicate(tx)}><Copy className="h-4 w-4" /></Button>
              <Button type="button" tone="danger" title="刪除" onClick={() => handleDelete(tx)}><Trash2 className="h-4 w-4" /></Button>
            </div>
          </article>
        )) : (
          <EmptyState title="尚無交易紀錄" description="新增買進、賣出或股利後，這裡會顯示交易卡片。" />
        )}
      </div>

      <DataTableShell className="hidden lg:block">
        <table className="w-full min-w-[50rem] table-fixed text-left text-sm">
          <colgroup>
            <col className="w-[5.333rem]" />
            <col className="w-[5.5rem]" />
            <col className="w-[3.333rem]" />
            <col className="w-[5.333rem]" />
            <col className="w-[7.875rem]" />
          </colgroup>
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="日期" sortKey="date" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="股票" sortKey="code" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="股數" sortKey="shares" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="成交價" sortKey="amount" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="原因" sortKey="reason" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {sortedItems.map((tx) => (
              <tr key={tx.id} className={`group ${editingId === tx.id ? "bg-teal-50/70" : "bg-panel/70 hover:bg-white/75"}`}>
                <td className="px-4 py-3 text-muted">{tx.date}</td>
                <td className="whitespace-normal break-words px-4 py-3 leading-5">{tx.code} {tx.name}</td>
                <td className="px-4 py-3 text-right">{tx.buy_shares ?? tx.sell_shares ?? "-"}</td>
                <td className={`px-4 py-3 text-right font-semibold ${signedAmountClass(signedTradeAmount(tx))}`}>
                  {signedMoney(signedTradeAmount(tx))}
                </td>
                <td className="relative whitespace-normal break-words px-4 py-3 leading-5 text-muted">
                  {tx.reason ?? ""}
                  <div className="pointer-events-none absolute right-4 top-1/2 z-20 flex -translate-y-1/2 justify-start">
                    <div className="pointer-events-auto inline-flex translate-y-1 items-center overflow-hidden rounded-2xl border border-line bg-white/95 opacity-0 shadow-soft transition duration-150 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100">
                      <button
                        type="button"
                        title="編輯"
                        onClick={() => handleEdit(tx)}
                        className="inline-flex h-10 w-14 items-center justify-center text-muted transition hover:bg-teal-50 hover:text-accent focus:bg-teal-50 focus:text-accent"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <span className="h-5 w-px bg-line" aria-hidden="true" />
                      <button
                        type="button"
                        title="複製"
                        onClick={() => handleDuplicate(tx)}
                        className="inline-flex h-10 w-14 items-center justify-center text-muted transition hover:bg-teal-50 hover:text-accent focus:bg-teal-50 focus:text-accent"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <span className="h-5 w-px bg-line" aria-hidden="true" />
                      <button
                        type="button"
                        title="刪除"
                        onClick={() => handleDelete(tx)}
                        className="inline-flex h-10 w-14 items-center justify-center text-muted transition hover:bg-rose-50 hover:text-rose-600 focus:bg-rose-50 focus:text-rose-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t border-line bg-white/95 text-[0.7rem] font-bold text-muted">
            <tr>
              <td className="px-4 py-2">{stats.count} 筆</td>
              <td className="px-4 py-2" />
              <td className="px-4 py-2" />
              <td className={`px-4 py-2 text-right ${signedAmountClass(stats.amount)}`}>{signedMoney(stats.amount)}</td>
              <td className="px-4 py-2" />
            </tr>
          </tfoot>
        </table>
      </DataTableShell>
    </section>
  );
}
