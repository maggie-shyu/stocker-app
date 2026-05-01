export type SortDirection = "asc" | "desc";

export function compareValues(a: string | number, b: string | number, dir: SortDirection) {
  if (typeof a === "string" && typeof b === "string") {
    return dir === "asc" ? a.localeCompare(b) : b.localeCompare(a);
  }

  return dir === "asc" ? Number(a) - Number(b) : Number(b) - Number(a);
}

export function sortItems<T>(
  items: readonly T[],
  getValue: (item: T) => string | number,
  dir: SortDirection,
) {
  return [...items].sort((left, right) => compareValues(getValue(left), getValue(right), dir));
}
