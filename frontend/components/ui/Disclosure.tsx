"use client";

import { useId, useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";

function ChevronIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden className="shrink-0">
      <path d="M3 4.5 6 7.5 9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * Progressive-disclosure primitive — the "simple at first glance, deep when
 * inspected" building block. Keyboard accessible toggle; content mounts on
 * open so collapsed content is never in the accessibility tree.
 */
export function Disclosure({
  title,
  defaultOpen = false,
  children,
  tone = "default",
  className,
  bodyClassName,
}: {
  title: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
  /** visual emphasis of the container */
  tone?: "default" | "muted";
  className?: string;
  bodyClassName?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const regionId = useId();
  const buttonId = useId();

  return (
    <div className={cn("rounded-card border border-hairline", tone === "muted" ? "bg-surfaceMuted" : "bg-surface", className)}>
      <h3 className="m-0">
        <button
          type="button"
          id={buttonId}
          onClick={() => setOpen((prev) => !prev)}
          aria-expanded={open}
          aria-controls={regionId}
          className="flex w-full items-center justify-between gap-3 rounded-card px-4 py-3 text-left text-sm font-medium text-ink transition-colors duration-fast ease-standard hover:bg-surfaceMuted"
        >
          <span>{title}</span>
          <span className={cn("grid h-5 w-5 place-items-center text-inkFaint transition-transform duration-fast ease-standard", open && "rotate-180")}>
            <ChevronIcon />
          </span>
        </button>
      </h3>
      {open && (
        <div id={regionId} role="region" aria-labelledby={buttonId} className="animate-rise-in">
          <div className={cn("border-t border-hairline px-4 py-4 text-sm text-inkMuted", bodyClassName)}>{children}</div>
        </div>
      )}
    </div>
  );
}
