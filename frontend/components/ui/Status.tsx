import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { resolveStatus, type StatusTone } from "@/lib/status";

type StatusKind = "auto" | "decision" | "outcome" | "risk";

export interface StatusProps {
  /** Raw value to auto-resolve (kind="auto") OR a controlled label when kind is set with tone */
  value?: string | null | undefined;
  kind?: StatusKind;
  /** Controlled tone/label when value is not auto-resolvable */
  tone?: StatusTone;
  label?: ReactNode;
  /** show a small status dot before the label */
  dot?: boolean;
  /** pill container (default) vs bare dot+label row */
  variant?: "pill" | "inline";
  className?: string;
}

/** Canonical semantic status. Never relies on color alone — always renders text. */
export function Status({ value, kind = "auto", tone, label, dot = false, variant = "pill", className }: StatusProps) {
  const resolved = resolveStatus(value);

  let resolvedTone: StatusTone;
  let resolvedLabel: ReactNode;

  if (kind !== "auto" && tone && label !== undefined) {
    // Fully controlled usage.
    resolvedTone = tone;
    resolvedLabel = label;
  } else if (kind !== "auto" && value !== undefined && value !== null) {
    // Keep text faithful to backend enum; tone maps from canonical category table.
    resolvedLabel = value;
    resolvedTone = resolveStatus(value).tone;
  } else {
    resolvedTone = resolved.tone;
    resolvedLabel = label ?? resolved.label;
  }

  const toneText = {
    neutral: "text-inkMuted",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
    info: "text-info",
  }[resolvedTone];

  const chipBg = {
    neutral: "border-neutralBorder bg-neutralBg",
    success: "border-successBorder bg-successBg",
    warning: "border-warningBorder bg-warningBg",
    danger: "border-dangerBorder bg-dangerBg",
    info: "border-infoBorder bg-infoBg",
  }[resolvedTone];

  const dotFill = {
    neutral: "bg-inkFaint",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
    info: "bg-info",
  }[resolvedTone];

  if (variant === "pill") {
    return (
      <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium", chipBg, toneText, className)}>
        {dot && <span aria-hidden className={cn("h-1.5 w-1.5 rounded-full", dotFill)} />}
        <span>{resolvedLabel}</span>
      </span>
    );
  }

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-sm font-medium", toneText, className)}>
      {dot && <span aria-hidden className={cn("h-1.5 w-1.5 rounded-full", dotFill)} />}
      <span>{resolvedLabel}</span>
    </span>
  );
}
