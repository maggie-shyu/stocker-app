import { Route, Routes } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { AdminPage } from "../features/admin/AdminPage";
import { AdminRouteGuard } from "../features/auth/AdminRouteGuard";
import { LoginPage } from "../features/auth/LoginPage";
import { RouteGuard } from "../features/auth/RouteGuard";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { HoldingsPage } from "../features/holdings/HoldingsPage";
import { CashFlowPage } from "../features/ledger/CashFlowPage";
import { RealizedPage } from "../features/ledger/RealizedPage";
import { TransactionsPage } from "../features/ledger/TransactionsPage";
import { AboutPage } from "../features/settings/AboutPage";
import { SettingsPage } from "../features/settings/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RouteGuard />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/holdings" element={<HoldingsPage />} />
          <Route path="/realized" element={<RealizedPage />} />
          <Route path="/cashflow" element={<CashFlowPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/settings/about" element={<AboutPage />} />
          <Route element={<AdminRouteGuard />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
