export function money(value?: number | null) {
  return Math.round(value ?? 0).toLocaleString("zh-TW");
}

export function shares(value?: number | null) {
  return Number(value ?? 0).toLocaleString("zh-TW", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  });
}

export function price(value?: number | null) {
  return Number(value ?? 0).toLocaleString("zh-TW", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

export function percent(value?: number | null) {
  const val = (value ?? 0) * 100;
  const formatted = val.toFixed(2);
  return val < 0 ? `${formatted}%` : `+${formatted}%`;
}

export function signedClass(value?: number | null) {
  if ((value ?? 0) > 0) return "text-gain";
  if ((value ?? 0) < 0) return "text-loss";
  return "text-muted";
}
