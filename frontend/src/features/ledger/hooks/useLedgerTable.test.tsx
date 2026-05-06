import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { formatVisibleRowRange, useLedgerTable } from "./useLedgerTable";

vi.mock("../../../platform/browser/useResponsivePageSize", () => ({
  useResponsivePageSize: () => 2,
}));

type Row = {
  id: string;
  amount: number;
  label: string;
};

const rows: Row[] = [
  { id: "a", amount: 30, label: "gamma" },
  { id: "b", amount: 10, label: "alpha" },
  { id: "c", amount: 20, label: "beta" },
];

describe("formatVisibleRowRange", () => {
  it("formats the empty state", () => {
    expect(formatVisibleRowRange(1, 25, 0)).toBe("顯示 0 筆");
  });

  it("formats the bounded visible range", () => {
    expect(formatVisibleRowRange(2, 25, 28)).toBe("顯示 26 - 28 筆");
  });
});

describe("useLedgerTable", () => {
  it("sorts with the configured default direction and paginates with the responsive page size", () => {
    const { result } = renderHook(() =>
      useLedgerTable({
        items: rows,
        initialSortKey: "amount",
        getSortValue: (item, sortKey) => item[sortKey as keyof Row] as string | number,
      }),
    );

    expect(result.current.pageSize).toBe(2);
    expect(result.current.totalPages).toBe(2);
    expect(result.current.sortedItems.map((item) => item.amount)).toEqual([30, 20, 10]);
    expect(result.current.paginatedItems.map((item) => item.id)).toEqual(["a", "c"]);
  });

  it("toggles direction for the same sort key and resets paging when the sort changes", () => {
    const { result } = renderHook(() =>
      useLedgerTable({
        items: rows,
        initialSortKey: "amount",
        getSortValue: (item, sortKey) => item[sortKey as keyof Row] as string | number,
      }),
    );

    act(() => {
      result.current.setPage(2);
    });
    act(() => {
      result.current.handleSort("amount");
    });

    expect(result.current.page).toBe(1);
    expect(result.current.sortDir).toBe("asc");
    expect(result.current.paginatedItems.map((item) => item.amount)).toEqual([10, 20]);
  });

  it("clamps page input and normalizes invalid committed values", () => {
    const { result } = renderHook(() =>
      useLedgerTable({
        items: rows,
        initialSortKey: "amount",
        getSortValue: (item, sortKey) => item[sortKey as keyof Row] as string | number,
      }),
    );

    act(() => {
      result.current.handlePageInputChange("9");
    });

    expect(result.current.page).toBe(2);
    expect(result.current.pageInput).toBe("2");

    act(() => {
      result.current.handlePageInputChange("oops");
    });
    act(() => {
      result.current.commitPageInput();
    });

    expect(result.current.page).toBe(1);
    expect(result.current.pageInput).toBe("1");
  });
});
