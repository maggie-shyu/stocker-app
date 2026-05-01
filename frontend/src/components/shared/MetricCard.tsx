import type { LucideIcon } from "lucide-react";

import { money, signedClass } from "./format";

type Props = {
  icon: LucideIcon;
  label: string;
  value: number;
  valueFormatter?: (value: number) => string;
  hint?: string;
  tone?: "neutral" | "signed";
  description?: string;
};

export function MetricCard({ icon: Icon, label, value, valueFormatter = money, hint, tone = "neutral", description }: Props) {
  return (
    <section className="group rounded-2xl border border-line/80 bg-panel/95 p-4 shadow-card transition hover:-translate-y-0.5 hover:shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-muted">{label}</span>
        <span className="rounded-xl bg-teal-50 p-2 text-accent transition group-hover:bg-teal-100">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </div>
      <div
        className={`mt-4 text-2xl font-bold tracking-tight sm:text-3xl ${
          tone === "signed" ? signedClass(value) : "text-ink"
        }`}
      >
        {valueFormatter(value)}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
        {hint ? <span className="rounded-full bg-white/80 px-2 py-1 font-semibold">{hint}</span> : null}
        {description ? <span>{description}</span> : null}
      </div>
    </section>
  );
}
