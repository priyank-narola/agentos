import type { ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";

export interface Crumb {
  label: ReactNode;
  href?: string;
}

/** Accessible breadcrumb navigation. */
export function Breadcrumbs({ items, className }: { items: Crumb[]; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={cn("min-w-0", className)}>
      <ol className="flex flex-wrap items-center gap-1.5 text-[13px]">
        {items.map((item, index) => {
          const last = index === items.length - 1;
          return (
            <li key={index} className="flex min-w-0 items-center gap-1.5">
              {item.href && !last ? (
                <Link href={item.href} className="truncate text-inkSubtle transition-colors duration-standard hover:text-ink">
                  {item.label}
                </Link>
              ) : (
                <span aria-current={last ? "page" : undefined} className={cn("truncate", last ? "font-medium text-ink" : "text-inkSubtle")}>
                  {item.label}
                </span>
              )}
              {!last && (
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden className="shrink-0 text-inkFaint">
                  <path d="m3 1.5 3.5 3.5L3 8.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
