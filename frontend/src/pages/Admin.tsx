
import { useEffect, useState } from "react";

import { Button, Card, EmptyState, PageHeader, SelectField, SkeletonBlock } from "../components/shared/UI";
import { useAdminOverview, useAdminTableData, useAdminTables } from "../hooks/queries";


function StatCard({
  title,
  value,
  description,
}: {
  title: string;
  value: number | null | undefined;
  description: string;
}) {
  return (
    <Card>
      <p className="text-sm font-semibold text-muted">{title}</p>
      <div className="mt-2 text-3xl font-bold tracking-tight text-ink">
        {value == null ? "Unavailable" : `${value.toFixed(1)}%`}
      </div>
      <p className="mt-2 text-sm text-muted">{description}</p>
    </Card>
  );
}


function formatBytes(value: number | null | undefined) {
  if (value == null) return "Unavailable";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let current = value;
  let unitIndex = 0;
  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024;
    unitIndex += 1;
  }
  return `${current.toFixed(1)} ${units[unitIndex]}`;
}

function formatVisibleRowRange(page: number, pageSize: number, total: number) {
  if (total <= 0) return "顯示 0 列";
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  return `顯示 ${start} - ${end} 列`;
}


export function Admin() {
  const overview = useAdminOverview();
  const tables = useAdminTables();
  const [selectedTable, setSelectedTable] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const tableData = useAdminTableData(selectedTable, page, pageSize, Boolean(selectedTable));

  useEffect(() => {
    if (!selectedTable && tables.data?.length) {
      setSelectedTable(tables.data[0].name);
    }
  }, [selectedTable, tables.data]);

  useEffect(() => {
    setPage(1);
  }, [selectedTable]);

  if (overview.isLoading || tables.isLoading) {
    return <SkeletonBlock label="載入管理介面中..." />;
  }

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Admin"
        title="Admin Console"
        description="集中查看 Supabase 資源狀態與全站資料概況，並瀏覽受控資料表。"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card>
          <p className="text-sm font-semibold text-muted">總使用者數</p>
          <div className="mt-2 text-3xl font-bold tracking-tight text-ink">{overview.data?.total_users?.toLocaleString() ?? "0"}</div>
          <p className="mt-2 text-sm text-muted">以 user settings rows 為基準。</p>
        </Card>
        <Card>
          <p className="text-sm font-semibold text-muted">有交易的使用者</p>
          <div className="mt-2 text-3xl font-bold tracking-tight text-ink">{overview.data?.users_with_transactions?.toLocaleString() ?? "0"}</div>
          <p className="mt-2 text-sm text-muted">曾建立至少一筆交易。</p>
        </Card>
        <Card>
          <p className="text-sm font-semibold text-muted">有出入金的使用者</p>
          <div className="mt-2 text-3xl font-bold tracking-tight text-ink">{overview.data?.users_with_cashflows?.toLocaleString() ?? "0"}</div>
          <p className="mt-2 text-sm text-muted">曾建立至少一筆出入金。</p>
        </Card>
        <StatCard title="RAM Usage" value={overview.data?.supabase_memory_usage_percent} description="來自 Supabase Metrics API 的記憶體使用率。" />
        <Card>
          <p className="text-sm font-semibold text-muted">Disk Space Used</p>
          <div className="mt-2 text-3xl font-bold tracking-tight text-ink">
            {formatBytes(overview.data?.database_space_used_bytes)}
          </div>
          <p className="mt-2 text-sm text-muted">來自 Supabase Metrics API 的資料庫實際使用空間。</p>
        </Card>
      </div>

      {overview.error ? (
        <EmptyState title="Supabase 指標暫時無法載入" description="請確認後端可以連到 Supabase Metrics API；缺少 memory 或 database size 指標時仍可使用資料表瀏覽。" />
      ) : null}

      <Card>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-bold text-ink">資料表瀏覽</h2>
              <p className="mt-1 text-sm text-muted">只提供受控資料表的唯讀瀏覽，不支援直接編輯或刪除。</p>
            </div>
            <div className="w-full lg:max-w-xs">
              {tables.error ? (
                <EmptyState title="資料表清單無法載入" description="請確認 admin API 可讀取受控資料表，或重新整理後再試一次。" />
              ) : (
                <SelectField
                  label="Choose Table"
                  value={selectedTable}
                  onChange={(event) => setSelectedTable(event.target.value)}
                >
                  {tables.data?.map((table) => (
                    <option key={table.name} value={table.name}>
                      {table.label}
                    </option>
                  ))}
                </SelectField>
              )}
            </div>
          </div>

          <div className="mt-4">
            <div className="rounded-2xl border border-line bg-white/75">
              <div className="border-b border-line px-4 py-3">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                  <h3 className="font-semibold text-ink">{tableData.data?.label ?? "資料表內容"}</h3>
                  <p className="mt-1 text-sm text-muted">
                      {formatVisibleRowRange(
                        tableData.data?.page ?? page,
                        tableData.data?.page_size ?? pageSize,
                        tableData.data?.total ?? 0,
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      max={Math.ceil((tableData.data?.total ?? 0) / pageSize) || 1}
                      value={page}
                      onChange={(e) => setPage(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-12 rounded-lg border border-line bg-white px-2 py-2 text-center text-sm font-semibold text-ink"
                      title="跳轉至特定頁"
                      disabled={tableData.isLoading}
                    />
                    <span className="text-sm font-semibold text-muted">/ {Math.ceil((tableData.data?.total ?? 0) / pageSize) || 1}</span>
                  </div>
                </div>
              </div>

              {tableData.error ? (
                <div className="p-4">
                  <EmptyState title="資料表內容無法載入" description="請確認選取的資料表存在，並檢查後端是否能用 service key 讀取它。" />
                </div>
              ) : tableData.isLoading ? (
                <div className="p-4">
                  <SkeletonBlock label="載入資料表內容中..." />
                </div>
              ) : tableData.data?.items.length ? (
                <div className="max-h-[34rem] overflow-auto">
                <table className="min-w-[1100px] divide-y divide-line text-sm">
                    <thead className="bg-stone-50/80">
                      <tr>
                        {tableData.data.columns.map((column) => (
                          <th key={column} className="sticky top-0 z-20 bg-stone-50/80 px-4 py-3 text-left font-semibold text-muted">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/70">
                      {tableData.data.items.map((row, index) => (
                        <tr key={`${row.id ?? index}`}>
                          {tableData.data?.columns.map((column) => (
                            <td key={column} className="px-4 py-3 align-top text-ink">
                              {String(row[column] ?? "")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4">
                  <EmptyState title="目前沒有可顯示的資料列" description="切換其他表格，或等系統累積更多資料。" />
                </div>
              )}
            </div>
          </div>
      </Card>
    </section>
  );
}
