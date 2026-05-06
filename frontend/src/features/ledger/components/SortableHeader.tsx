import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

type Props = {
  label: string;
  sortKey: string;
  activeKey: string;
  dir: "asc" | "desc";
  onSort: (key: string) => void;
  className?: string;
};

export function SortableHeader({ label, sortKey, activeKey, dir, onSort, className = "" }: Props) {
  const active = sortKey === activeKey;
  return (
    <th
      className={`cursor-pointer select-none px-4 py-3 font-bold tracking-wide text-muted transition hover:bg-white/70 ${className}`}
      onClick={() => onSort(sortKey)}
    >
      <span className={`inline-flex items-center gap-1 ${active ? "text-accent" : ""}`}>
        {label}
        {active
          ? dir === "asc"
            ? <ArrowUp className="h-3 w-3" />
            : <ArrowDown className="h-3 w-3" />
          : <ArrowUpDown className="h-3 w-3 opacity-40" />}
      </span>
    </th>
  );
}
