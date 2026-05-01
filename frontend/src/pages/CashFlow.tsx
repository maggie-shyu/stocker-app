import { Copy, Pencil, Plus, Trash2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import { portfolioQueryKeys, useInvalidateQueries } from "../api/query";
import type { Cashflow } from "../api/types";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Button, Card, DataTableShell, EmptyState, Field, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { money } from "../components/shared/format";
import { useCashflows } from "../hooks/queries";

const EMPTY_FORM = {
  date: new Date().toISOString().slice(0, 10),
  deposit: "",
  withdrawal: "",
};

function cashflowToForm(row: Cashflow) {
  return {
    date: row.date,
    deposit: String(row.deposit || ""),
    withdrawal: String(row.withdrawal || ""),
  };
}

export function CashFlow() {
  const { data, isLoading } = useCashflows();
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

  const sortedRows = useMemo(() => {
    const rows = data ?? [];
    return sortItems(rows, (row) => (row as unknown as Record<string, string | number>)[sortKey] ?? "", sortDir);
  }, [data, sortKey, sortDir]);

  const stats = useMemo(() => {
    const rows = data ?? [];
    return {
      count: rows.length,
      deposit: rows.reduce((sum, row) => sum + row.deposit, 0),
      withdrawal: rows.reduce((sum, row) => sum + row.withdrawal, 0),
    };
  }, [data]);

  const invalidateCashflow = () => {
    return invalidateQueries(portfolioQueryKeys);
  };

  const buildPayload = () => ({
    date: form.date,
    deposit: Number(form.deposit || 0),
    withdrawal: Number(form.withdrawal || 0),
    is_principal: false,
  });

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, date: new Date().toISOString().slice(0, 10) });
    setEditingId(null);
  };

  const createMutation = useMutation({
    mutationFn: async () => api.post("/cashflow", buildPayload()),
    onSuccess: () => {
      setForm((current) => ({ ...current, deposit: "", withdrawal: "" }));
      invalidateCashflow();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (id: number) => api.put(`/cashflow/${id}`, buildPayload()),
    onSuccess: () => {
      resetForm();
      invalidateCashflow();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/cashflow/${id}`),
    onSuccess: invalidateCashflow,
  });

  const handleEdit = (row: Cashflow) => {
    setEditingId(row.id);
    setForm(cashflowToForm(row));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDuplicate = (row: Cashflow) => {
    setEditingId(null);
    setForm({ ...cashflowToForm(row), date: new Date().toISOString().slice(0, 10) });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = (row: Cashflow) => {
    if (window.confirm(`確定要刪除 ${row.date} 這筆出入金？`)) deleteMutation.mutate(row.id);
  };

  if (isLoading) return <SkeletonBlock label="載入出入金資料中..." />;

  const principal = (data ?? []).reduce((sum, row) => sum + row.deposit - row.withdrawal, 0);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (editingId !== null) updateMutation.mutate(editingId);
    else createMutation.mutate();
  };

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Cash movement"
        title="出入金"
        description={
          <>
            目前本金 {money(principal)}。記錄投入與提領。
            {editingId !== null ? <span className="ml-2 font-semibold text-accent">正在編輯 #{editingId}</span> : null}
          </>
        }
        action={
          <>
            {editingId !== null ? <Button type="button" tone="secondary" onClick={resetForm}>取消</Button> : null}
            <Button form="cashflow-form">
              <Plus className="h-4 w-4" aria-hidden="true" />
              {editingId !== null ? "更新" : "新增"}
            </Button>
          </>
        }
      />

      <Card>
        <form id="cashflow-form" onSubmit={submit} className="grid gap-3 md:grid-cols-3">
          <Field label="日期" type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />
          <Field label="入金" inputMode="decimal" placeholder="入金" value={form.deposit} onChange={(event) => setForm({ ...form, deposit: event.target.value })} />
          <Field label="出金" inputMode="decimal" placeholder="出金" value={form.withdrawal} onChange={(event) => setForm({ ...form, withdrawal: event.target.value })} />
        </form>
      </Card>

      <div className="grid gap-3 lg:hidden">
        {sortedRows.length ? sortedRows.map((row: Cashflow) => (
          <article key={row.id} className={`rounded-2xl border bg-panel p-4 shadow-card ${editingId === row.id ? "border-accent" : "border-line"}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-bold">{row.date}</div>
              </div>
              <div className="text-right text-sm">
                <div className="font-bold text-gain">入金 {money(row.deposit)}</div>
                <div className="font-bold text-loss">出金 {money(row.withdrawal)}</div>
              </div>
            </div>
            <div className="mt-3 flex justify-end gap-1">
              <Button type="button" tone="ghost" title="編輯" onClick={() => handleEdit(row)}><Pencil className="h-4 w-4" /></Button>
              <Button type="button" tone="ghost" title="複製" onClick={() => handleDuplicate(row)}><Copy className="h-4 w-4" /></Button>
              <Button type="button" tone="danger" title="刪除" onClick={() => handleDelete(row)}><Trash2 className="h-4 w-4" /></Button>
            </div>
          </article>
        )) : (
          <EmptyState title="尚無出入金紀錄" description="新增第一筆入金後，這裡會顯示資金流。" />
        )}
      </div>

      <DataTableShell className="hidden lg:block">
        <table className="w-full min-w-[42rem] table-fixed text-left text-sm">
          <colgroup>
            <col className="w-[8rem]" />
            <col className="w-[8rem]" />
            <col className="w-[8rem]" />
          </colgroup>
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="日期" sortKey="date" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="入金" sortKey="deposit" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="出金" sortKey="withdrawal" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {sortedRows.map((row: Cashflow) => (
              <tr key={row.id} className={`group ${editingId === row.id ? "bg-teal-50/70" : "bg-panel/70 hover:bg-white/75"}`}>
                <td className="px-4 py-3">{row.date}</td>
                <td className="px-4 py-3 text-right font-semibold text-gain">{money(row.deposit)}</td>
                <td className="relative px-4 py-3 text-right font-semibold text-loss">
                  {money(row.withdrawal)}
                  <div className="pointer-events-none absolute right-4 top-1/2 z-20 flex -translate-y-1/2 justify-start">
                    <div className="pointer-events-auto inline-flex translate-y-1 items-center overflow-hidden rounded-2xl border border-line bg-white/95 opacity-0 shadow-soft transition duration-150 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100">
                      <button
                        type="button"
                        title="編輯"
                        onClick={() => handleEdit(row)}
                        className="inline-flex h-10 w-14 items-center justify-center text-muted transition hover:bg-teal-50 hover:text-accent focus:bg-teal-50 focus:text-accent"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <span className="h-5 w-px bg-line" aria-hidden="true" />
                      <button
                        type="button"
                        title="複製"
                        onClick={() => handleDuplicate(row)}
                        className="inline-flex h-10 w-14 items-center justify-center text-muted transition hover:bg-teal-50 hover:text-accent focus:bg-teal-50 focus:text-accent"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <span className="h-5 w-px bg-line" aria-hidden="true" />
                      <button
                        type="button"
                        title="刪除"
                        onClick={() => handleDelete(row)}
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
              <td className="px-4 py-2 text-right text-gain">{money(stats.deposit)}</td>
              <td className="px-4 py-2 text-right text-loss">{money(stats.withdrawal)}</td>
            </tr>
          </tfoot>
        </table>
      </DataTableShell>
    </section>
  );
}
