import { useEffect, useMemo, useState } from "react";

import { useResponsivePageSize } from "../../../platform/browser/useResponsivePageSize";
import { sortItems, type SortDirection } from "../lib/sort";

type Options<T> = {
  items: readonly T[];
  initialSortKey: string;
  initialSortDir?: SortDirection;
  getSortValue: (item: T, sortKey: string) => string | number;
};

export function formatVisibleRowRange(page: number, pageSize: number, total: number, unit = "筆") {
  if (total <= 0) {
    return `顯示 0 ${unit}`;
  }

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  return `顯示 ${start} - ${end} ${unit}`;
}

export function useLedgerTable<T>({
  items,
  initialSortKey,
  initialSortDir = "desc",
  getSortValue,
}: Options<T>) {
  const pageSize = useResponsivePageSize();
  const [sortKey, setSortKey] = useState(initialSortKey);
  const [sortDir, setSortDir] = useState<SortDirection>(initialSortDir);
  const [page, setPage] = useState(1);
  const [pageInput, setPageInput] = useState("1");

  const sortedItems = useMemo(() => {
    return sortItems(items, (item) => getSortValue(item, sortKey), sortDir);
  }, [getSortValue, items, sortDir, sortKey]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / pageSize));

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [page, pageSize, sortedItems]);

  useEffect(() => {
    setPageInput(String(page));
  }, [page]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const handleSort = (nextSortKey: string) => {
    if (nextSortKey === sortKey) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(nextSortKey);
      setSortDir("desc");
    }

    setPage(1);
  };

  const handlePageInputChange = (value: string) => {
    setPageInput(value);
    const pageNumber = Number.parseInt(value, 10);

    if (!Number.isNaN(pageNumber) && pageNumber >= 1) {
      setPage(Math.min(pageNumber, totalPages));
    }
  };

  const commitPageInput = () => {
    const pageNumber = Number.parseInt(pageInput, 10);
    const nextPage = Number.isNaN(pageNumber) ? 1 : Math.min(Math.max(pageNumber, 1), totalPages);

    setPage(nextPage);
    setPageInput(String(nextPage));
  };

  return {
    handlePageInputChange,
    handleSort,
    commitPageInput,
    page,
    pageInput,
    pageSize,
    paginatedItems,
    setPage,
    sortDir,
    sortKey,
    sortedItems,
    totalPages,
  };
}
