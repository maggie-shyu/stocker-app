export function money(value?: number | null) {
  return Math.round(value ?? 0).toLocaleString("zh-TW");
}

export function percent(value?: number | null) {
  return `${(((value ?? 0) * 100).toFixed(2))}%`;
}

export function signedClass(value?: number | null) {
  if ((value ?? 0) > 0) return "text-gain";
  if ((value ?? 0) < 0) return "text-loss";
  return "text-muted";
}
