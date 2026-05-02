import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { RouteGuard } from "./components/RouteGuard";
import { CashFlow } from "./pages/CashFlow";
import { Dashboard } from "./pages/Dashboard";
import { Holdings } from "./pages/Holdings";
import { Login } from "./pages/Login";
import { Realized } from "./pages/Realized";
import { Settings } from "./pages/Settings";
import { Transactions } from "./pages/Transactions";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 15_000
    }
  }
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RouteGuard />}>
            <Route element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/holdings" element={<Holdings />} />
              <Route path="/realized" element={<Realized />} />
              <Route path="/cashflow" element={<CashFlow />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
