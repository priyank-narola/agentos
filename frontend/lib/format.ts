/** Shared formatting helpers — single source of truth for display strings. */

/** Currency amount with proper locale + fractional digits. */
export function formatMoney(amount: number | string | null | undefined, currency = "USD"): string {
  const value = Number(amount ?? 0);
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency, minimumFractionDigits: 2 }).format(value);
  } catch {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(value);
  }
}

/** Whole or decimal number with thousand separators. */
export function formatNumber(value: number | string | null | undefined): string {
  const n = Number(value ?? 0);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(n);
}

/** Localized date + time (falls back gracefully on invalid input). */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

/** Short, screen-reader-friendly timestamp (time-only for dense rows). */
export function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString();
}

/** Compact identifier preview for dense tables: 8-char prefix + ellipsis. */
export function shortId(id: string | null | undefined, length = 8): string {
  if (!id) return "—";
  if (id.length <= length + 2) return id;
  return `${id.slice(0, length)}…`;
}

/** Percentage 0–1 → "12.3%". */
export function formatPercent(value: number | null | undefined, fractionDigits = 1): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${(Number(value) * 100).toFixed(fractionDigits)}%`;
}
