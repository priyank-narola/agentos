import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** Metric readout — label + large tabular value + note. */
export function Metric({
  label,
  value,
  note,
  tone = "default",
  className,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  tone?: "default" | "success" | "warning" | "danger";
  className?: string;
}) {
  const valueTone = {
    default: "text-ink",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  }[tone];
  return (
    <div className={cn("rounded-card border border-hairline bg-surface p-4 shadow-card", className)}>
      <p className="truncate text-xs font-medium text-inkSubtle">{label}</p>
      <p className={cn("tnum mt-2 text-3xl font-semibold tracking-tight", valueTone)}>{value}</p>
      {note && <p className="mt-1.5 text-[11px] leading-4 text-inkFaint">{note}</p>}
    </div>
  );
}

/** Compact inline metric (smaller value, used inside grouped strips). */
export function MetricInline({
  label,
  value,
  tone = "default",
  className,
}: {
  label: string;
  value: ReactNode;
  tone?: "default" | "success" | "warning" | "danger";
  className?: string;
}) {
  const valueTone = {
    default: "text-ink",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  }[tone];
  return (
    <div className={cn("min-w-0", className)}>
      <p className="text-[11px] font-medium uppercase tracking-wide text-inkFaint">{label}</p>
      <p className={cn("tnum mt-0.5 truncate text-base font-semibold tracking-tight", valueTone)}>{value}</p>
    </div>
  );
}
