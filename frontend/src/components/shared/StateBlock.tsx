export function StateBlock({ label }: { label: string }) {
  return (
    <div className="page-reveal rounded-2xl border border-line bg-panel/90 p-6 text-sm text-muted shadow-card">
      {label}
    </div>
  );
}
