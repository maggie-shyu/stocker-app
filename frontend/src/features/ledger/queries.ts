import { queryKeys, useApiQuery } from "../../platform/api/query";
import type { Cashflow, RealizedResponse, TransactionPage } from "./types";

export function useTransactions() {
  return useApiQuery<TransactionPage>(queryKeys.transactions, "/transactions", { page_size: 100 });
}

export function useCashflows() {
  return useApiQuery<Cashflow[]>(queryKeys.cashflows, "/cashflow");
}

export function useRealized() {
  return useApiQuery<RealizedResponse>(queryKeys.realized, "/realized");
}
