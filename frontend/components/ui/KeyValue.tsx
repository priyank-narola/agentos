import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface KeyValueItem {
  label: ReactNode;
  value?: ReactNode;
  /** render value in a monospace, breakable font */
  mono?: boolean;
  /** allow long values to wrap/break */
  wrap?: boolean;
  muted?: boolean;
}

/** Vertical list of label/value definition rows (dense, aligned). */
export function KeyValueList({ items, className }: { items: KeyValueItem[]; className?: string }) {
  return (
    <dl className={cn("divide-y divide-hairline", className)}>
      {items.map((item, index) => (
        <div key={index} className="grid grid-cols-[minmax(0,120px)_1fr] gap-4 py-2.5">
          <dt className="text-xs font-medium text-inkFaint">{item.label}</dt>
          <dd
            className={cn(
              "min-w-0 text-sm text-ink",
              item.mono && "font-mono text-[13px] tracking-tight",
              item.wrap && "break-words",
              item.muted && "text-inkSubtle",
            )}
          >
            {item.value ?? "—"}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Horizontal two-column grid of label → value fields (stat cards). */
export function KeyValueGrid({ items, className, minCols = 2 }: { items: KeyValueItem[]; className?: string; minCols?: number }) {
  const cols = minCols === 2 ? "sm:grid-cols-2" : minCols === 3 ? "sm:grid-cols-2 lg:grid-cols-3" : "sm:grid-cols-2 lg:grid-cols-4";
  return (
    <div className={cn("grid gap-3", cols, className)}>
      {items.map((item, index) => (
        <div key={index} className="rounded-card border border-hairline bg-surface p-3.5">
          <p className="text-[11px] font-medium uppercase tracking-wide text-inkFaint">{item.label}</p>
          <p
            className={cn(
              "mt-1.5 text-sm text-ink",
              item.mono && "font-mono text-[13px] tracking-tight",
              item.wrap && "break-words",
              item.muted && "text-inkSubtle",
            )}
          >
            {item.value ?? "—"}
          </p>
        </div>
      ))}
    </div>
  );
}
