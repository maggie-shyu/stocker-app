import { queryKeys, useApiQuery } from "../api/query";
import type {
  AdminCapabilities,
  AdminOverview,
  AdminTablePage,
  AdminTableSummary,
  Cashflow,
  UserSettings,
  Dashboard,
  Holding,
  RealizedResponse,
  TransactionPage
} from "../api/types";

export function useDashboard() {
  return useApiQuery<Dashboard>(queryKeys.dashboard, "/dashboard");
}

export function useTransactions() {
  return useApiQuery<TransactionPage>(queryKeys.transactions, "/transactions", { page_size: 100 });
}

export function useHoldings() {
  return useApiQuery<Holding[]>(queryKeys.holdings, "/holdings");
}

export function useRealized() {
  return useApiQuery<RealizedResponse>(queryKeys.realized, "/realized");
}

export function useCashflows() {
  return useApiQuery<Cashflow[]>(queryKeys.cashflows, "/cashflow");
}

export function useSettings() {
  return useApiQuery<UserSettings>(queryKeys.settings, "/settings");
}

export function useAdminCapabilities(enabled = true) {
  return useApiQuery<AdminCapabilities>(
    queryKeys.adminCapabilities,
    "/admin/capabilities",
    undefined,
    { enabled },
  );
}

export function useAdminOverview(enabled = true) {
  return useApiQuery<AdminOverview>(
    queryKeys.adminOverview,
    "/admin/overview",
    undefined,
    { enabled },
  );
}

export function useAdminTables(enabled = true) {
  return useApiQuery<AdminTableSummary[]>(
    queryKeys.adminTables,
    "/admin/tables",
    undefined,
    { enabled },
  );
}

export function useAdminTableData(tableName: string, page: number, pageSize: number, enabled = true) {
  return useApiQuery<AdminTablePage>(
    [...queryKeys.adminTableData, tableName],
    `/admin/tables/${tableName}`,
    { page, page_size: pageSize },
    { enabled: enabled && Boolean(tableName) },
  );
}
