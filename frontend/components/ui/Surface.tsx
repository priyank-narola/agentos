import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface SurfaceProps extends HTMLAttributes<HTMLElement> {
  /** visual emphasis */
  variant?: "default" | "muted" | "sunken" | "emphasis";
  /** semantic element */
  as?: "div" | "section" | "article" | "aside";
  children: ReactNode;
}

/** Primary content card — calm, hairline-bounded, subtly elevated. */
export function Surface({ variant = "default", as: Tag = "section", className, children, ...rest }: SurfaceProps) {
  const styles = {
    default: "border-hairline bg-surface shadow-card",
    muted: "border-hairline bg-surfaceMuted",
    sunken: "border-hairlineStrong bg-surfaceSunken",
    emphasis: "border-ink bg-ink text-white shadow-card",
  } as const;
  return (
    <Tag className={cn("rounded-card border", styles[variant], className)} {...rest}>
      {children}
    </Tag>
  );
}

/** Consistent card header block: eyebrow → title → supporting line + trailing action. */
export function SurfaceHeader({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string;
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-start justify-between gap-4", className)}>
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow text-inkFaint">{eyebrow}</p>}
        {title && <h2 className="mt-1 text-[17px] font-semibold tracking-tight text-ink">{title}</h2>}
        {description && <p className="mt-1 max-w-2xl text-sm leading-6 text-inkSubtle">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div>}
    </div>
  );
}

/** Section title used outside a card (page-level sub-blocks). */
export function SectionTitle({ eyebrow, title, description, className }: { eyebrow?: string; title?: ReactNode; description?: ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0", className)}>
      {eyebrow && <p className="eyebrow text-inkFaint">{eyebrow}</p>}
      {title && <h2 className="mt-0.5 text-base font-semibold tracking-tight text-ink">{title}</h2>}
      {description && <p className="mt-1 max-w-2xl text-sm leading-6 text-inkSubtle">{description}</p>}
    </div>
  );
}
