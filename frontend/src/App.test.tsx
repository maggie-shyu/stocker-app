import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
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
            holdings_pie: [
              { code: "3163", name: "波若威", market_value: 1070000, weight: 0.16 }
            ],
            recent_transactions: [],
            price_status: { total: 1, priced: 1, delayed: 0 }
          }
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
                id: 3,
                date: "2025-08-06",
                action: "買",
                code: "3130",
                name: "一零四",
                trade_type: "一般",
                buy_shares: 1000,
                buy_price: 224.5,
                current_price: 221,
                amount: 224500,
                expense: 224520,
                income: 0,
                reason: "test"
              }
            ]
          }
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
              weight: 0.16
            }
          ]
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
                income: 226797.5,
                cost_basis: 224520,
                realized_pnl: 2277.5,
                realized_pnl_rate: 0.01
              },
              {
                date: "2025-09-20",
                code: "3130",
                name: "一零四",
                shares: 500,
                income: 115500,
                cost_basis: 111000,
                realized_pnl: 4500,
                realized_pnl_rate: 0.0405
              }
            ],
            total_realized_pnl: 953960.27,
            dividend_income: 7506,
            invested_capital: 3974834.46,
            realized_pnl_rate: 0.24,
            dividend_realized_pnl_rate: 0.0079,
            win_rate: 0.72,
            avg_win: 85000,
            avg_loss: -12000
          }
        });
      }
      if (url === "/cashflow") {
        return Promise.resolve({
          data: [{ id: 2, date: "2025-08-04", deposit: 565554, withdrawal: 0 }]
        });
      }
      if (url === "/settings") {
        return Promise.resolve({ data: { commission_discount_rate: 0 } });
      }
      return Promise.resolve({ data: [] });
    }),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} }))
  }
}));

describe("App", () => {
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

    await user.click(screen.getByRole("link", { name: /已實現損益/ }));
    expect(await screen.findByRole("heading", { name: "已實現損益" })).toBeInTheDocument();
    expect(await screen.findByText("953,960")).toBeInTheDocument();
    expect((await screen.findAllByText("3130 一零四")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("335,520")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("342,298")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("6,778")).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /出入金/ }));
    expect(await screen.findByRole("heading", { name: "出入金" })).toBeInTheDocument();
    expect((await screen.findAllByText("565,554")).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /設定/ }));
    expect(await screen.findByRole("heading", { name: "設定" })).toBeInTheDocument();
    expect(await screen.findByText("手續費折數")).toBeInTheDocument();
  });

  it("submits settings, cashflow, and transaction forms", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("link", { name: /設定/ }));
    await user.click(await screen.findByRole("slider"));
    await user.click(await screen.findByRole("button", { name: "儲存" }));

    await user.click(screen.getByRole("link", { name: /出入金/ }));
    await user.clear(await screen.findByPlaceholderText("入金"));
    await user.type(screen.getByPlaceholderText("入金"), "1000");
    await user.click(screen.getByRole("button", { name: "新增" }));

    await user.click(screen.getByRole("link", { name: /交易紀錄/ }));
    await user.click(await screen.findByRole("button", { name: "股利" }));
    await user.type(await screen.findByPlaceholderText("代號"), "2330");
    await user.type(screen.getByPlaceholderText("股票"), "台積電");
    await user.type(screen.getByPlaceholderText("股利收入"), "1000");
    await user.click(screen.getByRole("button", { name: "新增" }));

    expect(await screen.findByText(/手續費/)).toBeInTheDocument();
  });
});
