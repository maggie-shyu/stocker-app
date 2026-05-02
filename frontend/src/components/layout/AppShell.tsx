import {
  Banknote,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Gauge,
  ListOrdered,
  PieChart,
  Settings,
  WalletCards
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const navGroups = [
  {
    label: "投資總覽",
    items: [
      { to: "/", label: "儀表板", icon: Gauge },
      { to: "/holdings", label: "持股狀況", icon: PieChart },
      { to: "/realized", label: "已實現損益", icon: BarChart3 },
    ],
  },
  {
    label: "交易管理",
    items: [
      { to: "/transactions", label: "交易紀錄", icon: ListOrdered },
      { to: "/cashflow", label: "出入金", icon: Banknote },
    ],
  },
  {
    label: "系統設定",
    items: [
      { to: "/settings", label: "設定", icon: Settings },
    ],
  },
];

export function AppShell() {
  const [isCollapsed, setIsCollapsed] = useState(true);

  return (
    <div className="min-h-screen bg-paper text-ink lg:flex">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_15%_10%,rgba(15,118,110,0.16),transparent_28rem),radial-gradient(circle_at_90%_0%,rgba(179,132,67,0.12),transparent_24rem)]" />
      <aside
        className={`relative border-b border-line/80 bg-panel/88 backdrop-blur-xl transition-all duration-300 lg:fixed lg:inset-y-0 lg:border-b-0 lg:border-r ${
          isCollapsed ? "lg:w-24" : "lg:w-72"
        }`}
      >
        <div className={`flex h-20 items-center gap-3 px-5 ${isCollapsed ? "lg:justify-center lg:px-3" : ""}`}>
          <div className="rounded-2xl bg-gradient-to-br from-moss to-accent p-3 text-white shadow-soft">
            <WalletCards className="h-6 w-6" aria-hidden="true" />
          </div>
          <div className={isCollapsed ? "lg:hidden" : ""}>
            <div className="text-xl font-black tracking-tight text-ink">Stocker</div>
            <div className="text-sm font-medium text-muted">Calm portfolio ledger</div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed((current) => !current)}
          className="absolute -right-5 top-48 z-20 hidden h-12 w-12 items-center justify-center rounded-full border border-line bg-white/95 text-ink shadow-soft transition hover:-translate-x-0.5 hover:bg-white lg:inline-flex"
          aria-label={isCollapsed ? "展開選單" : "收合選單"}
          title={isCollapsed ? "展開選單" : "收合選單"}
        >
          {isCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>

        <div className={`mx-5 border-t border-line/80 ${isCollapsed ? "lg:mx-3" : ""}`} />

        <nav className={`flex gap-2 overflow-x-auto px-3 pb-3 pt-4 lg:block lg:space-y-2 lg:overflow-visible ${isCollapsed ? "lg:px-3" : "lg:px-5"}`}>
          {navGroups.map((group) => (
            <section key={group.label} className="min-w-fit lg:min-w-0">
              <div className="flex gap-2 lg:block lg:space-y-1">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    title={item.label}
                    className={({ isActive }) =>
                      `flex min-w-fit items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm font-bold transition ${
                        isCollapsed ? "lg:min-w-0 lg:justify-center lg:px-0" : ""
                      } ${
                        isActive
                          ? "bg-white/95 text-accent shadow-sm ring-1 ring-line"
                          : "text-muted hover:bg-white/70 hover:text-ink"
                      }`
                    }
                  >
                    <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                    <span className={isCollapsed ? "lg:hidden" : ""}>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </section>
          ))}
        </nav>
      </aside>
      <main
        className={`w-full min-w-0 px-4 py-5 transition-all duration-300 sm:px-6 lg:px-8 lg:py-8 ${
          isCollapsed ? "lg:ml-24 lg:w-[calc(100%-6rem)]" : "lg:ml-72 lg:w-[calc(100%-18rem)]"
        }`}
      >
        <div className="mx-auto max-w-7xl page-reveal">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
