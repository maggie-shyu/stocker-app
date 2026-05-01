import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";

export const queryKeys = {
  dashboard: ["dashboard"] as const,
  transactions: ["transactions"] as const,
  holdings: ["holdings"] as const,
  realized: ["realized"] as const,
  cashflows: ["cashflows"] as const,
  settings: ["settings"] as const,
};

export function useApiQuery<T>(queryKey: readonly string[], path: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...queryKey, params ?? null],
    queryFn: async () => (await api.get<T>(path, params ? { params } : undefined)).data,
  });
}

export function useInvalidateQueries() {
  const queryClient = useQueryClient();

  return (keys: ReadonlyArray<readonly string[]>) =>
    Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey: [...queryKey] })));
}

export const portfolioQueryKeys = [
  queryKeys.dashboard,
  queryKeys.transactions,
  queryKeys.holdings,
  queryKeys.realized,
  queryKeys.cashflows,
] as const;
