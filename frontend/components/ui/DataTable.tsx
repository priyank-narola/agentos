import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface DataColumn<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
  align?: "left" | "right" | "center";
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  /** whole-row navigation/selection (adds affordance styling + chevron column) */
  onRowClick?: (row: T) => void;
  /** semantic table caption for screen readers */
  caption?: string;
  empty?: ReactNode;
  /** add horizontal scroll + a sensible min width for dense tables */
  scroll?: boolean;
  minWidth?: number;
  className?: string;
}

/**
 * Accessible data-table foundation. Real <table> semantics (header scope,
 * caption), overflow-safe on small viewports, optional row click affordance.
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  caption,
  empty,
  scroll = true,
  minWidth = 680,
  className,
}: DataTableProps<T>) {
  const alignClass = { left: "text-left", right: "text-right", center: "text-center" } as const;

  if (rows.length === 0 && empty) {
    return <div>{empty}</div>;
  }

  const table = (
    <table className={cn("w-full border-collapse text-sm", className)}>
      {caption && <caption className="sr-only">{caption}</caption>}
      <thead>
        <tr className="border-b border-hairline bg-surfaceMuted">
          {columns.map((col) => (
            <th
              key={col.key}
              scope="col"
              className={cn(
                "px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-inkFaint",
                alignClass[col.align ?? "left"],
                col.headerClassName,
              )}
            >
              {col.header}
            </th>
          ))}
          {onRowClick && <th scope="col" className="w-8 px-2 py-2.5" aria-label="Open" />}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={rowKey(row)}
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            tabIndex={onRowClick ? 0 : undefined}
            onKeyDown={
              onRowClick
                ? (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onRowClick(row);
                    }
                  }
                : undefined
            }
            role={onRowClick ? "button" : undefined}
            aria-label={onRowClick ? "Open record" : undefined}
            className={cn(
              "border-b border-hairline last:border-0",
              onRowClick && "cursor-pointer transition-colors duration-standard hover:bg-surfaceMuted focus-visible:bg-surfaceMuted",
            )}
          >
            {columns.map((col) => (
              <td key={col.key} className={cn("px-4 py-3 align-top", alignClass[col.align ?? "left"], col.className)}>
                {col.render(row)}
              </td>
            ))}
            {onRowClick && (
              <td className="px-2 py-3 text-right text-inkFaint">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden className="inline-block">
                  <path d="m5 2.5 4.5 4.5L5 11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );

  if (scroll) {
    return (
      <div className="overflow-hidden rounded-card border border-hairline bg-surface shadow-card">
        <div className="overflow-x-auto" style={minWidth ? { minWidth: undefined } : undefined}>
          <div style={{ minWidth }}>{table}</div>
        </div>
      </div>
    );
  }

  return <div className="overflow-hidden rounded-card border border-hairline bg-surface shadow-card">{table}</div>;
}
