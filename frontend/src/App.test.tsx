import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const { apiGetMock, apiPostMock, apiPutMock, apiDeleteMock, authState } = vi.hoisted(() => ({
  authState: {
    isAdmin: true,
  },
  apiGetMock: vi.fn((url: string, config?: { params?: Record<string, string | number> }) => {
    if (url === "/admin/capabilities") {
      return Promise.resolve({ data: { is_admin: authState.isAdmin } });
    }
    if (url === "/admin/overview") {
      return Promise.resolve({
        data: {
          total_users: 3,
          users_with_transactions: 2,
          users_with_cashflows: 2,
          supabase_memory_usage_percent: 58.0,
          cpu_busy_percent: 42.0,
          disk_usage_percent: 75.0,
          connection_rate_percent: 70.0,
          active_queries: 12,
        },
      });
    }
    if (url === "/admin/tables") {
      return Promise.resolve({
        data: [
          {
            name: "transactions",
            label: "交易紀錄",
            description: "All transaction rows across users.",
            row_count: 5,
          },
          {
            name: "user_settings",
            label: "使用者設定",
            description: "Per-user settings rows.",
            row_count: 3,
          },
        ],
      });
    }
    if (url === "/admin/tables/transactions") {
      const page = Number(config?.params?.page ?? 1);
      return Promise.resolve({
        data: {
          table_name: "transactions",
          label: "交易紀錄",
          page,
          page_size: 25,
          total: 73,
          columns: ["id", "user_id", "code"],
          items: page === 2
            ? [
                { id: "tx-26", user_id: "user-26", code: "2603" },
                { id: "tx-27", user_id: "user-27", code: "0050" },
              ]
            : [
                { id: "tx-1", user_id: "user-1", code: "2330" },
                { id: "tx-2", user_id: "user-2", code: "2317" },
              ],
        },
      });
    }
    if (url === "/dashboard") {
      return Promise.resolve({
        data: {
          account_value: 6547207.8,
          principal: 2670399,
          investment_years: 1.92,
          stock_market_value: 6363700,
          cash_balance: 183507.8,
          unrealized_pnl: 1500000,
          unrealized_pnl_rate: 0.3,
          realized_pnl: 953960.27,
          realized_pnl_rate: 0.24,
          account_pnl: 3876808.8,
          account_pnl_rate: 1.45,
          annualized_return_rate: 0.59,
          today_pnl: 0,
          dividend_income: 7506,
          holdings_pie: [{ code: "3163", name: "波若威", market_value: 1070000, weight: 0.16 }],
          recent_transactions: [],
          price_status: { total: 1, priced: 1, delayed: 0 },
        },
      });
    }
    if (url === "/transactions") {
      return Promise.resolve({
        data: {
          total: 1,
          page: 1,
          page_size: 100,
          items: [
            {
              id: "3",
              date: "2025-08-06",
              action: "買",
              code: "3130",
              name: "一零四",
              trade_type: "一般",
              buy_shares: 1000,
              buy_price: 224.5,
              current_price: 221,
              discounted_fee: 20,
              tax: 0,
              amount: 224500,
              expense: 224520,
              income: 0,
              reason: "test",
            },
          ],
        },
      });
    }
    if (url === "/admin/tables/user_settings") {
      const page = Number(config?.params?.page ?? 1);
      return Promise.resolve({
        data: {
          table_name: "user_settings",
          label: "使用者設定",
          page,
          page_size: 25,
          total: 3,
          columns: ["user_id", "display_name"],
          items: [
            { user_id: "user-a", display_name: "Maggie" },
            { user_id: "user-b", display_name: "Alex" },
            { user_id: "user-c", display_name: "Jamie" },
          ],
        },
      });
    }
    if (url === "/holdings") {
      return Promise.resolve({
        data: [
          {
            code: "3163",
            name: "波若威",
            lots: [{ date: "2025-09-19", shares: 1000, cost_per_share: 224.02, cost_basis: 224020 }],
            total_shares: 1000,
            avg_cost: 224.02,
            current_price: 1070,
            market_value: 1070000,
            cost_basis: 224020,
            unrealized_pnl: 845980,
            unrealized_pnl_rate: 3.77,
            weight: 0.16,
          },
        ],
      });
    }
    if (url === "/realized") {
      return Promise.resolve({
        data: {
          items: [
            {
              date: "2025-09-12",
              code: "3130",
              name: "一零四",
              shares: 1000,
              avg_buy_price: 224.5,
              avg_sell_price: 227,
              income: 226797.5,
              cost_basis: 224520,
              realized_pnl: 2277.5,
              realized_pnl_rate: 0.01,
            },
            {
              date: "2025-09-20",
              code: "3130",
              name: "一零四",
              shares: 500,
              avg_buy_price: 222,
              avg_sell_price: 231,
              income: 115500,
              cost_basis: 111000,
              realized_pnl: 4500,
              realized_pnl_rate: 0.0405,
            },
          ],
          dividend_by_stock: [
            {
              code: "3130",
              name: "一零四",
              dividend_income: 7506,
            },
          ],
          total_realized_pnl: 953960.27,
          dividend_income: 7506,
          invested_capital: 3974834.46,
          realized_pnl_rate: 0.24,
          dividend_realized_pnl_rate: 0.0079,
          win_rate: 0.72,
          avg_win: 85000,
          avg_loss: -12000,
        },
      });
    }
    if (url === "/cashflow") {
      return Promise.resolve({
        data: [{ id: "2", date: "2025-08-04", deposit: 565554, withdrawal: 0 }],
      });
    }
    if (url === "/settings") {
      return Promise.resolve({ data: { commission_discount_rate: 0 } });
    }
    if (url === "/stocks/search") {
      const query = String(config?.params?.q ?? "");
      if (query === "2330") return Promise.resolve({ data: [{ code: "2330", name: "台積電" }] });
      if (query === "台積電") return Promise.resolve({ data: [{ code: "2330", name: "台積電" }] });
      if (query === "23") {
        return Promise.resolve({
          data: [
            { code: "2330", name: "台積電" },
            { code: "2303", name: "聯電" },
          ],
        });
      }
      if (query === "台") {
        return Promise.resolve({
          data: [
            { code: "2330", name: "台積電" },
            { code: "2303", name: "聯電" },
          ],
        });
      }
      return Promise.resolve({ data: [] });
    }
    if (url === "/stocks/preview-fee") {
      return Promise.resolve({
        data: {
          discounted_fee: 20,
          expense: 100020,
        },
      });
    }
    return Promise.resolve({ data: [] });
  }) as any,
  apiPostMock: vi.fn(() => Promise.resolve({ data: {} })),
  apiPutMock: vi.fn(() => Promise.resolve({ data: {} })),
  apiDeleteMock: vi.fn(() => Promise.resolve({ data: {} })),
}));

vi.mock("./contexts/AuthContext", () => ({
  useAuth: () => ({
    session: { access_token: "test-token", user: { email: "admin@example.com" } },
    loading: false,
    configError: null,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
    updatePassword: vi.fn(),
  }),
}));

vi.mock("./api/client", () => ({
  api: {
    get: apiGetMock,
    post: apiPostMock,
    put: apiPutMock,
    delete: apiDeleteMock,
  },
}));

describe("App", () => {
  beforeEach(() => {
    authState.isAdmin = true;
    window.history.pushState({}, "", "/");
  });

  it("renders the dashboard shell and KPI cards", async () => {
    render(<App />);

    expect(await screen.findByText("Stocker")).toBeInTheDocument();
    expect((await screen.findAllByText("帳戶淨值")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("6,547,208")).length).toBeGreaterThan(0);
    expect(await screen.findByText("1/1 檔已有報價")).toBeInTheDocument();
    expect(await screen.findByText("年化報酬率")).toBeInTheDocument();
    expect(await screen.findByText("59.00%")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /交易紀錄/ })).toBeInTheDocument();
  });

  it("renders transactions, holdings, realized, cashflow, and settings routes", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("link", { name: /交易紀錄/ }));
    expect(await screen.findByRole("heading", { name: "交易紀錄" })).toBeInTheDocument();
    expect((await screen.findAllByText(/3130/)).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /持股狀況/ }));
    expect(await screen.findByRole("heading", { name: "持股狀況" })).toBeInTheDocument();
    expect((await screen.findAllByText(/波若威/)).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /平倉盈虧/ }));
    expect(await screen.findByRole("heading", { name: "平倉盈虧" })).toBeInTheDocument();
    expect(await screen.findByText("953,960")).toBeInTheDocument();
    expect((await screen.findAllByText("3130 一零四")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("賣均")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("買均")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("6,778")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("7,506")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("14,284")).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /資金異動/ }));
    expect(await screen.findByRole("heading", { name: "資金異動" })).toBeInTheDocument();
    expect((await screen.findAllByText("565,554")).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /設定/ }));
    expect(await screen.findByRole("heading", { name: "設定" })).toBeInTheDocument();
    expect(await screen.findByText("手續費設定")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Open Admin" })).toBeInTheDocument();
  });

  it("renders the admin console for admin users", async () => {
    authState.isAdmin = true;
    window.history.pushState({}, "", "/admin");

    render(<App />);

    expect(await screen.findByRole("heading", { name: "管理者後台" })).toBeInTheDocument();
    expect(await screen.findByText("總使用者數")).toBeInTheDocument();
    expect(await screen.findByText("CPU Usage")).toBeInTheDocument();
    expect(await screen.findByText("Disk Usage")).toBeInTheDocument();
    expect(await screen.findByText("Connection Rate")).toBeInTheDocument();
    expect(await screen.findByText("Active Queries")).toBeInTheDocument();
    expect(await screen.findByDisplayValue("交易紀錄")).toBeInTheDocument();
    expect(await screen.findByText("75.0%")).toBeInTheDocument();
    expect(await screen.findByText("顯示 1 - 25 列")).toBeInTheDocument();
  });

  it("paginates the admin table and requests later pages", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/admin");
    render(<App />);

    expect(await screen.findByText("顯示 1 - 25 列")).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: "下一頁" }));

    expect(apiGetMock).toHaveBeenCalledWith(
      "/admin/tables/transactions",
      expect.objectContaining({
        params: expect.objectContaining({
          page: 2,
          page_size: 25,
        }),
      }),
    );
    expect(await screen.findByText("2603")).toBeInTheDocument();
    expect(await screen.findByText("顯示 26 - 50 列")).toBeInTheDocument();
  });

  it("switches the selected admin table and reloads the matching rows", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/admin");
    render(<App />);

    const select = await screen.findByLabelText("Choose Table");
    await user.selectOptions(select, "user_settings");

    expect(apiGetMock).toHaveBeenCalledWith(
      "/admin/tables/user_settings",
      expect.objectContaining({
        params: expect.objectContaining({
          page: 1,
          page_size: 25,
        }),
      }),
    );
    expect(await screen.findByRole("heading", { name: "使用者設定" })).toBeInTheDocument();
    expect(await screen.findByText("顯示 1 - 3 列")).toBeInTheDocument();
    expect(await screen.findByText("Maggie")).toBeInTheDocument();
  });

  it("redirects non-admin users away from the admin route", async () => {
    authState.isAdmin = false;
    window.history.pushState({}, "", "/admin");

    render(<App />);

    expect(await screen.findByText("Stocker")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /儀表板/ })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Admin Console" })).not.toBeInTheDocument();
    authState.isAdmin = true;
  });

  it("submits settings, cashflow, and transaction forms", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("link", { name: /設定/ }));
    await user.click(await screen.findByRole("button", { name: "調整手續費" }));
    await user.click(await screen.findByRole("button", { name: "儲存" }));

    await user.click(screen.getByRole("link", { name: /資金異動/ }));
    await user.clear(await screen.findByPlaceholderText("入金"));
    await user.type(screen.getByPlaceholderText("入金"), "1000");
    await user.click(screen.getByRole("button", { name: "新增" }));

    await user.click(screen.getByRole("link", { name: /交易紀錄/ }));
    await user.click(await screen.findByRole("button", { name: "股利" }));
    await user.type(await screen.findByPlaceholderText("代號"), "2330");
    await user.type(screen.getByPlaceholderText("股票"), "台積電");
    await user.type(screen.getByPlaceholderText("股利收入"), "1000");
    await user.click(screen.getByRole("button", { name: "新增" }));

    expect((await screen.findAllByText(/手續費/)).length).toBeGreaterThan(0);
  });

  it("syncs stock code and name in both directions and keeps fee preview params intact", async () => {
    const user = userEvent.setup();
    apiGetMock.mockClear();
    render(<App />);

    await user.click(await screen.findByRole("link", { name: /交易紀錄/ }));

    const codeInput = await screen.findByPlaceholderText("代號");
    const nameInput = await screen.findByPlaceholderText("股票");
    const sharesInput = await screen.findByPlaceholderText("股數");
    const priceInput = await screen.findByPlaceholderText("價格");

    await user.clear(codeInput);
    await user.type(codeInput, "23");
    expect(await screen.findByText("台積電")).toBeInTheDocument();
    await user.click(screen.getAllByText("台積電")[0]);
    expect(codeInput).toHaveValue("2330");
    expect(nameInput).toHaveValue("台積電");

    await user.clear(nameInput);
    await user.type(nameInput, "台積電");
    await screen.findByDisplayValue("2330");
    expect(codeInput).toHaveValue("2330");

    await user.clear(sharesInput);
    await user.type(sharesInput, "1000");
    await user.clear(priceInput);
    await user.type(priceInput, "100");

    expect(apiGetMock).toHaveBeenCalledWith(
      "/stocks/preview-fee",
      expect.objectContaining({
        params: expect.objectContaining({
          action: "買",
          trade_type: "一般",
          shares: 1000,
          amount: 100000,
        }),
      })
    );
  });

  it("ignores stale stock search responses so the latest exact input still wins", async () => {
    const user = userEvent.setup();
    apiGetMock.mockImplementation((url: string, config?: { params?: Record<string, string | number> }) => {
      if (url !== "/stocks/search") {
        if (url === "/dashboard") {
          return Promise.resolve({
            data: {
              account_value: 6547207.8,
              principal: 2670399,
              investment_years: 1.92,
              stock_market_value: 6363700,
              cash_balance: 183507.8,
              unrealized_pnl: 1500000,
              unrealized_pnl_rate: 0.3,
              realized_pnl: 953960.27,
              realized_pnl_rate: 0.24,
              account_pnl: 3876808.8,
              account_pnl_rate: 1.45,
              annualized_return_rate: 0.59,
              today_pnl: 0,
              dividend_income: 7506,
              holdings_pie: [{ code: "3163", name: "波若威", market_value: 1070000, weight: 0.16 }],
              recent_transactions: [],
              price_status: { total: 1, priced: 1, delayed: 0 },
            },
          });
        }
        if (url === "/transactions") {
          return Promise.resolve({ data: { total: 0, page: 1, page_size: 100, items: [] } });
        }
        if (url === "/holdings") return Promise.resolve({ data: [] });
        if (url === "/realized") {
          return Promise.resolve({
            data: {
              items: [],
              dividend_by_stock: [],
              total_realized_pnl: 0,
              dividend_income: 0,
              invested_capital: 0,
              realized_pnl_rate: 0,
              dividend_realized_pnl_rate: 0,
              win_rate: 0,
              avg_win: 0,
              avg_loss: 0,
            },
          });
        }
        if (url === "/cashflow") return Promise.resolve({ data: [] });
        if (url === "/settings") return Promise.resolve({ data: { commission_discount_rate: 0, base_commission_rate: 0.001425, minimum_fee: 20, odd_lot_minimum_fee: 1, stock_tax_rate: 0.003, day_trade_tax_rate: 0.0015, etf_tax_rate: 0.001, bond_etf_tax_rate: 0 } });
        if (url === "/stocks/preview-fee") {
          return Promise.resolve({ data: { discounted_fee: 20, expense: 100020 } });
        }
        return Promise.resolve({ data: [] });
      }

      const query = String(config?.params?.q ?? "");
      if (query === "2") {
        return new Promise((resolve) =>
          setTimeout(() => resolve({ data: [{ code: "2330", name: "台積電" }, { code: "2303", name: "聯電" }] }), 300)
        );
      }
      if (query === "23") {
        return new Promise((resolve) =>
          setTimeout(() => resolve({ data: [{ code: "2330", name: "台積電" }, { code: "2303", name: "聯電" }] }), 250)
        );
      }
      if (query === "233") {
        return new Promise((resolve) =>
          setTimeout(() => resolve({ data: [{ code: "2330", name: "台積電" }] }), 200)
        );
      }
      if (query === "2330") {
        return new Promise((resolve) =>
          setTimeout(() => resolve({ data: [{ code: "2330", name: "台積電" }] }), 50)
        );
      }
      return Promise.resolve({ data: [] });
    });

    render(<App />);
    await user.click(await screen.findByRole("link", { name: /交易紀錄/ }));

    const codeInput = await screen.findByPlaceholderText("代號");
    const nameInput = await screen.findByPlaceholderText("股票");

    await user.type(codeInput, "2330");
    await screen.findByDisplayValue("台積電");

    expect(codeInput).toHaveValue("2330");
    expect(nameInput).toHaveValue("台積電");
  });
});
