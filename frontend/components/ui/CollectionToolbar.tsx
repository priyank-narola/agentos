import type { ReactNode } from "react";

/**
 * Adapted from Paperclip's `ui/src/components/CollectionToolbar.tsx`.
 *
 * Copyright (c) 2025 Paperclip AI. Licensed under MIT; see
 * THIRD_PARTY_NOTICES.md for the complete notice and source reference.
 * The component is presentation-only so AgentOS retains ownership of all
 * state, API calls, authorization, and governance behavior.
 */
export function CollectionToolbar({
  context,
  search,
  controls,
  actions,
  feedback,
  className = "",
  ariaLabel = "Collection controls",
}: {
  context?: ReactNode;
  search?: ReactNode;
  controls?: ReactNode;
  actions?: ReactNode;
  feedback?: ReactNode;
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <div className={`flex flex-col gap-2 ${className}`} role="toolbar" aria-label={ariaLabel}>
      <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center">
        {context ? <div className="min-w-0 shrink-0">{context}</div> : null}
        {search ? <div className="min-w-0 flex-1">{search}</div> : null}
        {controls || actions ? <div className="flex min-w-0 flex-wrap items-center gap-1 sm:ml-auto sm:flex-nowrap">{controls ? <div className="flex min-w-0 flex-wrap items-center gap-1">{controls}</div> : null}{actions ? <div className="flex shrink-0 items-center gap-1">{actions}</div> : null}</div> : null}
      </div>
      {feedback ? <div className="min-w-0">{feedback}</div> : null}
    </div>
  );
}
