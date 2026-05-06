import { queryKeys, useApiQuery } from "../../platform/api/query";
import type {
  AdminCapabilities,
  AdminOverview,
  AdminTablePage,
  AdminTableSummary,
} from "./types";

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
