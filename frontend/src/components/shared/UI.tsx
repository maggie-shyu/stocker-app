import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type Tone = "primary" | "secondary" | "ghost" | "danger";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function Card({
  children,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <section
      className={cx(
        "rounded-2xl border border-line/80 bg-panel/95 shadow-card backdrop-blur",
        padded && "p-4 sm:p-5",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function Button({
  children,
  className = "",
  tone = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone }) {
  const tones: Record<Tone, string> = {
    primary: "bg-accent text-white shadow-soft hover:bg-teal-800",
    secondary: "border border-line bg-white/80 text-ink hover:bg-white",
    ghost: "text-muted hover:bg-white/70 hover:text-ink",
    danger: "text-rose-700 hover:bg-rose-50",
  };

  return (
    <button
      className={cx(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55",
        tones[tone],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function PageHeader({
  title,
  eyebrow,
  description,
  action,
}: {
  title: string;
  eyebrow?: string;
  description?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow ? (
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.22em] text-accent">{eyebrow}</p>
        ) : null}
        <h1 className="text-2xl font-bold tracking-tight text-ink sm:text-3xl">{title}</h1>
        {description ? <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{description}</p> : null}
      </div>
      {action ? <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div> : null}
    </header>
  );
}

const fieldBase =
  "min-h-11 w-full rounded-xl border border-line bg-white/85 px-3 py-2 text-sm text-ink shadow-sm transition placeholder:text-stone-400 focus:border-accent focus:bg-white focus:ring-2 focus:ring-accent/15";

export function Field({
  label,
  hint,
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  return (
    <label className={cx("block space-y-1.5", className)}>
      <span className="text-xs font-bold uppercase tracking-[0.14em] text-muted">{label}</span>
      <input className={fieldBase} {...props} />
      {hint ? <span className="block text-xs text-muted">{hint}</span> : null}
    </label>
  );
}

export function SelectField({
  label,
  children,
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) {
  return (
    <label className={cx("block space-y-1.5", className)}>
      <span className="text-xs font-bold uppercase tracking-[0.14em] text-muted">{label}</span>
      <select className={fieldBase} {...props}>
        {children}
      </select>
    </label>
  );
}

export function DataTableShell({
  children,
  className = "",
  scrollClassName = "",
}: {
  children: ReactNode;
  className?: string;
  scrollClassName?: string;
}) {
  return (
    <div className={cx("overflow-hidden rounded-2xl border border-line bg-panel shadow-card", className)}>
      <div className={cx("overflow-x-auto", scrollClassName)}>{children}</div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-white/60 p-6 text-center">
      <p className="font-semibold text-ink">{title}</p>
      {description ? <p className="mt-2 text-sm text-muted">{description}</p> : null}
    </div>
  );
}

export function SkeletonBlock({ label = "載入中..." }: { label?: string }) {
  return (
    <div className="page-reveal space-y-4">
      <div className="h-24 animate-pulse rounded-3xl border border-line bg-white/60" aria-label={label} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="h-32 animate-pulse rounded-2xl border border-line bg-white/55" />
        ))}
      </div>
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "warn" | "accent";
}) {
  const tones = {
    neutral: "border-line bg-white/80 text-muted",
    good: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
    accent: "border-teal-200 bg-teal-50 text-teal-800",
  };

  return (
    <span className={cx("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold", tones[tone])}>
      {children}
    </span>
  );
}
