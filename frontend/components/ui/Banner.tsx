import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import type { StatusTone } from "@/lib/status";

export interface BannerProps {
  tone?: StatusTone;
  title?: ReactNode;
  children?: ReactNode;
  /** true when the content announces a blocking/safety condition */
  alert?: boolean;
  className?: string;
}

const TONES: Record<StatusTone, { box: string; title: string; body: string }> = {
  neutral: { box: "border-hairline bg-surface", title: "text-ink", body: "text-inkSubtle" },
  info: { box: "border-infoBorder bg-infoBg", title: "text-info", body: "text-inkMuted" },
  success: { box: "border-successBorder bg-successBg", title: "text-success", body: "text-inkMuted" },
  warning: { box: "border-warningBorder bg-warningBg", title: "text-warning", body: "text-inkMuted" },
  danger: { box: "border-dangerBorder bg-dangerBg", title: "text-danger", body: "text-inkMuted" },
};

/** Tonal message band. `alert` adds role=alert for screen readers. */
export function Banner({ tone = "neutral", title, children, alert = false, className }: BannerProps) {
  const t = TONES[tone];
  return (
    <div
      role={alert && (tone === "danger" || tone === "warning") ? "alert" : undefined}
      className={cn("rounded-card border px-4 py-3", t.box, className)}
    >
      {title && <p className={cn("text-sm font-semibold", t.title)}>{title}</p>}
      {children && <div className={cn("mt-0.5 text-sm leading-6", title ? t.body : t.title)}>{children}</div>}
    </div>
  );
}

/** Single canonical sandbox indicator — the ONLY sandbox marker foundation. */
export function SandboxBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-warningBorder bg-warningBg px-2.5 py-0.5 text-[11px] font-semibold text-warning",
        className,
      )}
    >
      <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-warning" />
      Sandbox · no real money
    </span>
  );
}
