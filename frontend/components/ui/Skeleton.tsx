import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

/** Base skeleton block. Reduced-motion handling is global (globals.css). */
export function Skeleton({ className, style }: { className?: string; style?: CSSProperties }) {
  return <div aria-hidden className={cn("animate-pulse rounded-control bg-surfaceSunken", className)} style={style} />;
}

/** Skeleton variants for common layouts. */
export const SkeletonText = ({ lines = 1, className }: { lines?: number; className?: string }) => (
  <div className={cn("space-y-2", className)}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} className={cn("h-3", i === lines - 1 ? "w-2/3" : "w-full")} />
    ))}
  </div>
);

export const SkeletonCard = ({ className }: { className?: string }) => (
  <div className={cn("rounded-card border border-hairline bg-surface p-5", className)}>
    <Skeleton className="h-3 w-1/3" />
    <Skeleton className="mt-4 h-7 w-1/2" />
    <Skeleton className="mt-3 h-3 w-2/3" />
  </div>
);

export const SkeletonRow = ({ columns = 4, className }: { columns?: number; className?: string }) => (
  <div className={cn("grid gap-4 px-5 py-4", className)} style={{ gridTemplateColumns: `repeat(${columns}, minmax(0,1fr))` }}>
    {Array.from({ length: columns }).map((_, i) => (
      <Skeleton key={i} className="h-3" />
    ))}
  </div>
);
