import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import type { StatusTone } from "@/lib/status";

/** Simple tonal label chip (non-status tags, metadata, sensitivity). */
export function Badge({
  children,
  tone = "neutral",
  className,
  mono = false,
}: {
  children: ReactNode;
  tone?: StatusTone;
  mono?: boolean;
  className?: string;
}) {
  const styles: Record<StatusTone, string> = {
    neutral: "border-neutralBorder bg-neutralBg text-inkMuted",
    success: "border-successBorder bg-successBg text-success",
    warning: "border-warningBorder bg-warningBg text-warning",
    danger: "border-dangerBorder bg-dangerBg text-danger",
    info: "border-infoBorder bg-infoBg text-info",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4",
        mono && "font-mono tracking-tight",
        styles[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
