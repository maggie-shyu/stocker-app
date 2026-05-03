import { Copy, Pencil, Plus, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import { portfolioQueryKeys, useInvalidateQueries } from "../api/query";
import type { Cashflow } from "../api/types";
import { SortableHeader } from "../components/shared/SortableHeader";
import { sortItems } from "../components/shared/sort";
import { Button, Card, EmptyState, Field, PageHeader, SkeletonBlock } from "../components/shared/UI";
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
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingRowNumber, setEditingRowNumber] = useState<number | null>(null);
  const [sortKey, setSortKey] = useState("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageInput, setPageInput] = useState("1");
  const [pageSize, setPageSize] = useState(window.innerWidth >= 1024 ? 25 : 10);

  useEffect(() => {
    const handleResize = () => {
      setPageSize(window.innerWidth >= 1024 ? 25 : 10);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const style = document.createElement("style");
    style.innerHTML = `
      input[type="number"]::-webkit-outer-spin-button,
      input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
      }
      input[type="number"] {
        -moz-appearance: textfield;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  useEffect(() => { setPageInput(String(page)); }, [page]);

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
    setPage(1);
  };

  const sortedRows = useMemo(() => {
    const rows = data ?? [];
    return sortItems(rows, (row) => (row as unknown as Record<string, string | number>)[sortKey] ?? "", sortDir);
  }, [data, sortKey, sortDir]);

  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, page, pageSize]);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
    if (page > totalPages) setPage(totalPages);
  }, [page, pageSize, sortedRows.length]);

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
  });

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, date: new Date().toISOString().slice(0, 10) });
    setEditingId(null);
    setEditingRowNumber(null);
  };

  const createMutation = useMutation({
    mutationFn: async () => api.post("/cashflow", buildPayload()),
    onSuccess: () => {
      setForm((current) => ({ ...current, deposit: "", withdrawal: "" }));
      invalidateCashflow();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (id: string) => api.put(`/cashflow/${id}`, buildPayload()),
    onSuccess: () => {
      resetForm();
      invalidateCashflow();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/cashflow/${id}`),
    onSuccess: invalidateCashflow,
  });

  const handleEdit = (row: Cashflow, rowNumber: number) => {
    setEditingId(row.id);
    setEditingRowNumber(rowNumber);
    setForm(cashflowToForm(row));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDuplicate = (row: Cashflow) => {
    setEditingId(null);
    setEditingRowNumber(null);
    setForm({ ...cashflowToForm(row), date: new Date().toISOString().slice(0, 10) });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = (row: Cashflow) => {
    if (window.confirm(`確定要刪除 ${row.date} 這筆資金異動？`)) deleteMutation.mutate(row.id);
  };

  if (isLoading) return <SkeletonBlock label="載入資金異動資料中..." />;

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
        title="資金異動"
        description={
          <>
            目前本金 {money(principal)}。記錄投入與提領。
            {editingRowNumber !== null ? <span className="ml-2 font-semibold text-accent">正在編輯 第 {editingRowNumber} 列</span> : null}
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
          <Field className="min-w-0" label="日期" type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />
          <Field label="入金" inputMode="decimal" placeholder="入金" value={form.deposit} onChange={(event) => setForm({ ...form, deposit: event.target.value })} />
          <Field label="出金" inputMode="decimal" placeholder="出金" value={form.withdrawal} onChange={(event) => setForm({ ...form, withdrawal: event.target.value })} />
        </form>
      </Card>

      <div className="rounded-2xl border border-line bg-white/75">
        <div className="border-b border-line px-4 py-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="font-semibold text-ink">明細列表</h3>
              <p className="mt-1 text-sm text-muted">
                {sortedRows.length <= 0 ? "顯示 0 筆" : `顯示 ${(page - 1) * pageSize + 1} - ${Math.min(page * pageSize, sortedRows.length)} 筆`}
              </p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-lg font-semibold text-muted hover:text-ink disabled:opacity-50"
              >
                ‹
              </button>
              <input
                type="number"
                min="1"
                max={Math.ceil(sortedRows.length / pageSize) || 1}
                value={pageInput}
                onChange={(e) => {
                  const val = e.target.value;
                  setPageInput(val);
                  const num = parseInt(val);
                  if (!isNaN(num) && num >= 1) setPage(num);
                }}
                onBlur={() => {
                  const num = parseInt(pageInput);
                  const valid = isNaN(num) ? 1 : Math.max(1, num);
                  setPage(valid);
                  setPageInput(String(valid));
                }}
                className="w-12 rounded-lg border border-line bg-white px-2 py-2 text-center text-sm font-semibold text-ink"
                title="跳轉至特定頁"
              />
              <span className="text-sm font-semibold text-muted">/ {Math.ceil(sortedRows.length / pageSize) || 1}</span>
              <button
                type="button"
                onClick={() => setPage(Math.min(Math.ceil(sortedRows.length / pageSize) || 1, page + 1))}
                disabled={page >= Math.ceil(sortedRows.length / pageSize)}
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-lg font-semibold text-muted hover:text-ink disabled:opacity-50"
              >
                ›
              </button>
            </div>
          </div>
        </div>

        <div className="grid gap-3 p-4 lg:hidden">
          {paginatedRows.length ? paginatedRows.map((row: Cashflow, index) => {
            const rowNumber = (page - 1) * pageSize + index + 1;
            return (
            <article key={row.id} className="rounded-2xl border border-line bg-panel p-4 shadow-card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-bold">{row.date}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-gain">入金 {money(row.deposit)}</div>
                  <div className="font-bold text-loss">出金 {money(row.withdrawal)}</div>
                </div>
              </div>
              <div className="mt-3 flex gap-2 border-t border-line pt-3">
                <button onClick={() => handleEdit(row, rowNumber)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-teal-50 hover:text-accent transition">
                  <Pencil className="h-3 w-3" /> 編輯
                </button>
                <button onClick={() => handleDuplicate(row)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-teal-50 hover:text-accent transition">
                  <Copy className="h-3 w-3" /> 複製
                </button>
                <button onClick={() => handleDelete(row)} className="flex items-center gap-1 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-loss hover:bg-red-50 transition">
                  <Trash2 className="h-3 w-3" /> 刪除
                </button>
              </div>
            </article>
            );
          }) : (
            <EmptyState title="尚無資金異動紀錄" description="新增第一筆入金後，這裡會顯示資金流。" />
          )}
        </div>

        <div className="relative z-0 hidden overflow-x-auto overflow-y-visible lg:block">
        <table className="w-full min-w-[38rem] table-fixed text-left text-sm">
          <colgroup>
            <col className="w-[7rem]" />
            <col className="w-[7rem]" />
            <col className="w-[7rem]" />
          </colgroup>
          <thead className="bg-white/55 text-xs uppercase">
            <tr>
              <SortableHeader label="日期" sortKey="date" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95" />
              <SortableHeader label="入金" sortKey="deposit" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
              <SortableHeader label="出金" sortKey="withdrawal" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="sticky top-0 z-20 bg-white/95 text-right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {paginatedRows.map((row: Cashflow, index) => {
              const rowNumber = (page - 1) * pageSize + index + 1;
              return (
              <tr key={row.id} className="group relative bg-panel/70 hover:bg-white/75">
                <td className="px-4 py-3">{row.date}</td>
                <td className="px-4 py-3 text-right font-semibold text-gain">{money(row.deposit)}</td>
                <td className="px-4 py-3 text-right font-semibold text-loss">
                  {money(row.withdrawal)}
                  <div className="absolute inset-y-0 right-2 hidden items-center gap-1 group-hover:flex">
                    <button
                      onClick={() => handleEdit(row, rowNumber)}
                      title="編輯"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-ink shadow-sm hover:bg-teal-50 hover:text-accent transition"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDuplicate(row)}
                      title="複製"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-ink shadow-sm hover:bg-teal-50 hover:text-accent transition"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(row)}
                      title="刪除"
                      className="flex items-center gap-1 rounded-lg border border-line bg-white px-2 py-1 text-xs font-semibold text-loss shadow-sm hover:bg-red-50 transition"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
              );
            })}
          </tbody>
          <tfoot className="border-t border-line bg-white/95 text-[0.7rem] font-bold text-muted">
            <tr>
              <td className="px-4 py-2">{stats.count} 筆</td>
              <td className="px-4 py-2 text-right text-gain">{money(stats.deposit)}</td>
              <td className="px-4 py-2 text-right text-loss">{money(stats.withdrawal)}</td>
            </tr>
          </tfoot>
        </table>
        </div>
      </div>
    </section>
  );
}
