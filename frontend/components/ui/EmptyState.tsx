import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** Content-less state with guidance + optional action (never relies on text alone). */
export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-card border border-dashed border-hairlineStrong bg-surface px-6 py-10 text-center", className)}>
      {icon && <div className="mb-3 grid h-10 w-10 place-items-center rounded-card border border-hairline bg-surfaceMuted text-inkFaint">{icon}</div>}
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && <p className="mt-1 max-w-md text-[13px] leading-5 text-inkSubtle">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Inline empty copy block used where a full EmptyState is too heavy. */
export function EmptyCopy({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("rounded-card border border-dashed border-hairline bg-surface px-4 py-3 text-sm text-inkSubtle", className)}>{children}</p>;
}
