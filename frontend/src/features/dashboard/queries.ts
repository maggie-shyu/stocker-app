import { useApiQuery, queryKeys } from "../../platform/api/query";
import type { Dashboard } from "./types";

export function useDashboard() {
  return useApiQuery<Dashboard>(queryKeys.dashboard, "/dashboard");
}
