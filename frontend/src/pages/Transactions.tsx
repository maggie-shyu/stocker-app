import { Copy, Pencil, Plus, Trash2, Wand2 } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { portfolioQueryKeys, useInvalidateQueries } from "../api/query";
import type { Transaction } from "../api/types";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Badge, Button, Card, EmptyState, Field, PageHeader, SelectField, SkeletonBlock } from "../components/shared/UI";
import { money, price } from "../components/shared/format";
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

function tradeShares(tx: Transaction) {
  return tx.buy_shares ?? tx.sell_shares ?? 0;
}

function tradePrice(tx: Transaction) {
  return tx.buy_price ?? tx.sell_price ?? 0;
}

function signedCashflow(tx: Transaction) {
  if (tx.action === "買") return -tx.expense;
  return tx.income;
}

function tradeFeeBreakdown(tx: Transaction) {
  const discountedFee = tx.discounted_fee ?? 0;
  const tax = tx.tax ?? 0;
  const parts = [];
  if (discountedFee > 0) parts.push(`手續費 ${money(discountedFee)}`);
  if (tax > 0) parts.push(`稅金 ${money(tax)}`);
  return parts.join(" · ");
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

function formatVisibleRowRange(page: number, pageSize: number, total: number) {
  if (total <= 0) return "顯示 0 筆";
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  return `顯示 ${start} - ${end} 筆`;
}

const INPUT =
  "min-h-11 w-full rounded-xl border border-line bg-white/85 px-3 py-2 text-sm text-ink shadow-sm transition placeholder:text-stone-400 focus:border-accent focus:bg-white focus:ring-2 focus:ring-accent/15";

export function Transactions() {
  const { data, isLoading } = useTransactions();
  const invalidateQueries = useInvalidateQueries();

  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
    setPage(1);
  };

  const sortedItems = useMemo(() => {
    const items = data?.items ?? [];
    return sortItems(items, (tx) => {
      if (sortKey === "shares") return tx.buy_shares ?? tx.sell_shares ?? 0;
      if (sortKey === "price") return tradePrice(tx);
      if (sortKey === "cashflow") return signedCashflow(tx);
      return (tx as unknown as Record<string, string | number>)[sortKey] ?? "";
    }, sortDir);
  }, [data, sortKey, sortDir]);

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page]);

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    return {
      count: items.length,
      amount: items.reduce((sum, tx) => sum + signedCashflow(tx), 0),
    };
  }, [data]);

  const [suggestions, setSuggestions] = useState<{ code: string; name: string }[]>([]);
  const [activeSuggestionField, setActiveSuggestionField] = useState<"code" | "name" | null>(null);
  const stockFieldsRef = useRef<HTMLDivElement>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();
  const latestSearchRequestId = useRef(0);
  const formRef = useRef(form);

  useEffect(() => {
    formRef.current = form;
  }, [form]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (stockFieldsRef.current && !stockFieldsRef.current.contains(e.target as Node)) {
        setActiveSuggestionField(null);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const fetchSuggestions = useCallback((query: string, field: "code" | "name") => {
    clearTimeout(searchTimer.current);
    latestSearchRequestId.current += 1;
    const requestId = latestSearchRequestId.current;
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      setSuggestions([]);
      setActiveSuggestionField(null);
      return;
    }

    searchTimer.current = setTimeout(async () => {
      const res = await api.get<{ code: string; name: string }[]>("/stocks/search", { params: { q: query } });
      const currentValue = (
        field === "code" ? formRef.current.code : formRef.current.name
      ).trim().toLowerCase();

      if (requestId !== latestSearchRequestId.current || currentValue !== normalizedQuery) {
        return;
      }

      const exactMatches = res.data.filter((stock) => {
        const target = field === "code" ? stock.code : stock.name;
        return target.trim().toLowerCase() === normalizedQuery;
      });

      if (exactMatches.length === 1) {
        const [exact] = exactMatches;
        setForm((f) => ({
          ...f,
          code: exact.code,
          name: exact.name,
        }));
        setSuggestions([]);
        setActiveSuggestionField(null);
        return;
      }

      setForm((f) => ({
        ...f,
        ...(field === "code" ? { name: "" } : { code: "" }),
      }));
      setSuggestions(res.data);
      setActiveSuggestionField(res.data.length > 0 ? field : null);
    }, 200);
  }, []);

  const handleNameChange = (value: string) => {
    setForm((f) => ({ ...f, name: value }));
    fetchSuggestions(value, "name");
  };

  const handleCodeChange = useCallback((value: string) => {
    setForm((f) => ({ ...f, code: value }));
    fetchSuggestions(value, "code");
  }, [fetchSuggestions]);

  const selectStock = (stock: { code: string; name: string }) => {
    setForm((f) => ({ ...f, code: stock.code, name: stock.name }));
    setSuggestions([]);
    setActiveSuggestionField(null);
  };

  const amount = useMemo(() => {
    if (form.action === "股利") return Number(form.dividend_income || 0);
    return Number(form.shares || 0) * Number(form.price || 0);
  }, [form.action, form.dividend_income, form.price, form.shares]);
  const shares = useMemo(() => Number(form.shares || 0), [form.shares]);

  const preview = useQuery({
    queryKey: ["fee-preview", form.action, form.code, form.trade_type, shares, amount],
    enabled: amount > 0,
    queryFn: async () =>
      (
        await api.get("/stocks/preview-fee", {
          params: { action: form.action, code: form.code, trade_type: form.trade_type, shares, amount },
        })
      ).data,
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
    mutationFn: (id: string) => api.put(`/transactions/${id}`, buildPayload()),
    onSuccess: () => {
      resetForm();
      invalidateAll();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/transactions/${id}`),
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

      <Card className="relative z-40">
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

          <div ref={stockFieldsRef} className="relative z-30 grid gap-3 lg:grid-cols-6">
            <Field label="日期" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            <div className="relative space-y-1.5">
              <span className="text-xs font-bold uppercase tracking-[0.14em] text-muted">代號</span>
              <input
                className={INPUT}
                placeholder="代號"
                value={form.code}
                onChange={(e) => handleCodeChange(e.target.value)}
                onFocus={() => form.code && suggestions.length > 0 && setActiveSuggestionField("code")}
                required
              />
              {activeSuggestionField === "code" ? (
                <ul className="absolute left-0 top-full z-50 mt-1 max-h-52 w-64 overflow-y-auto rounded-xl border border-line bg-white shadow-lg">
                  {suggestions.map((s) => (
                    <li
                      key={`${s.code}-${s.name}-code`}
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
            <div className="relative space-y-1.5">
              <span className="text-xs font-bold uppercase tracking-[0.14em] text-muted">股票名稱</span>
              <input
                className={INPUT}
                placeholder="股票"
                value={form.name}
                onChange={(e) => handleNameChange(e.target.value)}
                onFocus={() => form.name && suggestions.length > 0 && setActiveSuggestionField("name")}
                required
              />
              {activeSuggestionField === "name" ? (
                <ul className="absolute left-0 top-full z-50 mt-1 max-h-52 w-64 overflow-y-auto rounded-xl border border-line bg-white shadow-lg">
                  {suggestions.map((s) => (
                    <li
                      key={`${s.code}-${s.name}-name`}
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

      <div className="rounded-2xl border border-line bg-white/75">
        <div className="border-b border-line px-4 py-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="font-semibold text-ink">明細列表</h3>
              <p className="mt-1 text-sm text-muted">
                {formatVisibleRowRange(page, pageSize, sortedItems.length)}
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
          {paginatedItems.length ? paginatedItems.map((tx) => (
            <article key={tx.id} className="rounded-2xl border border-line bg-panel p-4 shadow-card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-bold">{tx.code} {tx.name}</div>
                  <p className="mt-1 text-sm text-muted">{tx.date} · {tx.action}</p>
                </div>
                <div className={`text-right font-bold ${signedAmountClass(signedCashflow(tx))}`}>
                  {signedMoney(signedCashflow(tx))}
                  <div className="text-xs">{tx.buy_shares ?? tx.sell_shares ?? "-"} 股</div>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-muted">股價</div>
                  <div className="mt-1 font-semibold text-ink">{tradePrice(tx) ? price(tradePrice(tx)) : "-"}</div>
                </div>
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-muted">費用</div>
                  <div className="mt-1 font-semibold text-ink">{tradeFeeBreakdown(tx) || "股息"}</div>
                </div>
              </div>
              {tx.reason ? (
                <div className="mt-3 rounded-lg border border-line bg-white/50 p-2 text-xs text-muted">
                  <span className="font-semibold">原因:</span> {tx.reason}
                </div>
              ) : null}
              <div className="mt-3 flex gap-2 border-t border-line pt-3">
                <button onClick={() => handleEdit(tx)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-teal-50 hover:text-accent transition">
                  <Pencil className="h-3 w-3" /> 編輯
                </button>
                <button onClick={() => handleDuplicate(tx)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-teal-50 hover:text-accent transition">
                  <Copy className="h-3 w-3" /> 複製
                </button>
                <button onClick={() => handleDelete(tx)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-loss hover:bg-red-50 transition">
                  <Trash2 className="h-3 w-3" /> 刪除
                </button>
              </div>
            </article>
          )) : (
            <EmptyState title="尚無交易紀錄" description="新增買進、賣出或股利後，這裡會顯示交易卡片。" />
          )}
        </div>

        <div className="relative z-0 hidden overflow-x-auto overflow-y-visible lg:block">
          <table className="w-full min-w-[45rem] table-fixed text-left text-sm">
            <colgroup>
            <col className="w-[4rem]" />
            <col className="w-[7rem]" />
            <col className="w-[3rem]" />
            <col className="w-[3rem]" />
            <col className="w-[5rem]" />
          </colgroup>
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="日期" sortKey="date" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="股票" sortKey="code" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="股數" sortKey="shares" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="股價" sortKey="price" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="收支" sortKey="cashflow" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {paginatedItems.map((tx) => (
              <tr key={tx.id} className="group relative bg-panel/70 hover:bg-white/75">
                <td className="px-4 py-3 text-muted">{tx.date}</td>
                <td className="px-4 py-3">{tx.code} {tx.name}</td>
                <td className="px-4 py-3 text-right">{tradeShares(tx) || "-"}</td>
                <td className="px-4 py-3 text-right">{tradePrice(tx) ? price(tradePrice(tx)) : "-"}</td>
                <td className={`px-4 py-3 text-right font-semibold ${signedAmountClass(signedCashflow(tx))}`}>
                  <div>{signedMoney(signedCashflow(tx))}</div>
                  <div className="mt-1 text-xs font-normal text-muted">{tradeFeeBreakdown(tx) || "股息"}</div>
                  <div className="absolute inset-y-0 right-2 hidden items-center gap-1 group-hover:flex">
                    <button
                      onClick={() => handleEdit(tx)}
                      title="編輯"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-ink shadow-sm hover:bg-teal-50 hover:text-accent transition"
                    >
                      <Pencil className="h-3 w-3" /> 編輯
                    </button>
                    <button
                      onClick={() => handleDuplicate(tx)}
                      title="複製"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-ink shadow-sm hover:bg-teal-50 hover:text-accent transition"
                    >
                      <Copy className="h-3 w-3" /> 複製
                    </button>
                    <button
                      onClick={() => handleDelete(tx)}
                      title="刪除"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-loss shadow-sm hover:bg-red-50 transition"
                    >
                      <Trash2 className="h-3 w-3" /> 刪除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t border-line bg-white/95 text-[0.7rem] font-bold text-muted">
            <tr>
                <td className="px-4 py-3">{stats.count} 筆</td>
                <td className="px-4 py-3" />
                <td className="px-4 py-3" />
                <td className="px-4 py-3" />
                <td className={`px-4 py-3 text-right ${signedAmountClass(stats.amount)}`}>{signedMoney(stats.amount)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>
  );
}
