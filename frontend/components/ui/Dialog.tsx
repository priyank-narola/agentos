"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { cn } from "@/lib/cn";

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="m3 3 8 8m0-8-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Accessible modal dialog foundation: focus management, Escape to close,
 * backdrop dismissal, scroll lock, and ARIA wiring.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  labelledBy,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  /** optional custom id of an element that names the dialog */
  labelledBy?: string;
  className?: string;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const panel = panelRef.current;
    const focusables = panel?.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusables && focusables.length > 0 ? focusables[0] : panel;
    first?.focus();
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
      previouslyFocused?.focus();
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto p-4">
      <div aria-hidden className="fixed inset-0 bg-ink/40 backdrop-blur-[2px]" onClick={onClose} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy ?? (title ? titleId : undefined)}
        aria-describedby={description ? descId : undefined}
        className={cn("relative w-full max-w-lg rounded-dialog border border-hairline bg-surface p-6 shadow-dialog", className)}
      >
        <div className={cn("flex items-start justify-between gap-4", Boolean(title || description) && "border-b border-hairline pb-4")}>
          <div className="min-w-0">
            {title && (
              <h2 id={titleId} className="text-lg font-semibold tracking-tight text-ink">
                {title}
              </h2>
            )}
            {description && (
              <p id={descId} className="mt-1 text-sm leading-6 text-inkSubtle">
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-control text-inkFaint transition-colors duration-standard hover:bg-surfaceMuted hover:text-ink"
          >
            <CloseIcon />
          </button>
        </div>
        {children && <div className="pt-4">{children}</div>}
        {footer && <div className="mt-5 flex flex-wrap items-center justify-end gap-2 border-t border-hairline pt-4">{footer}</div>}
      </div>
    </div>
  );
}
