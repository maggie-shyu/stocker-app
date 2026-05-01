import { queryKeys, useApiQuery } from "../api/query";
import type {
  Cashflow,
  CommissionSettings,
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
  return useApiQuery<CommissionSettings>(queryKeys.settings, "/settings");
}
