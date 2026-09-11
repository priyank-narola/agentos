"use client";

import { useId, useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Lightweight accessible tooltip. Shown on hover AND keyboard focus of the
 * trigger (wrap an interactive element so focus events fire). The tooltip
 * itself is supplementary — it never carries meaning on its own.
 */
export function Tooltip({ label, children, className }: { label: ReactNode; children: ReactNode; className?: string }) {
  const [visible, setVisible] = useState(false);
  const tipId = useId();

  return (
    <span
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span
          id={tipId}
          role="tooltip"
          className="pointer-events-none absolute bottom-full left-1/2 z-30 mb-1.5 w-max max-w-[240px] -translate-x-1/2 rounded-popover border border-hairline bg-ink px-2.5 py-1.5 text-center text-xs font-normal leading-5 text-white shadow-elevated"
        >
          {label}
        </span>
      )}
    </span>
  );
}
