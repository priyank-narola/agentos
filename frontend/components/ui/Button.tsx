import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "dark";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** leading icon/content (no icon library — pass an inline SVG or node) */
  leadingIcon?: ReactNode;
  children: ReactNode;
}

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-signal text-white hover:bg-signalHover disabled:bg-inkFaint/40 disabled:text-white/80",
  secondary: "border border-hairlineStrong bg-surface text-ink hover:bg-surfaceMuted disabled:text-inkFaint disabled:hover:bg-surface",
  ghost: "text-signal hover:bg-signalSoft disabled:text-inkFaint disabled:hover:bg-transparent",
  danger: "bg-danger text-white hover:brightness-95 disabled:bg-inkFaint/40 disabled:text-white/80",
  dark: "bg-ink text-white hover:bg-ink/90 disabled:bg-inkFaint/40 disabled:text-white/80",
};

const SIZES: Record<ButtonSize, string> = {
  sm: "min-h-[32px] rounded-control px-3 text-[13px] gap-1.5",
  md: "min-h-[38px] rounded-control px-4 text-sm gap-2",
  lg: "min-h-[46px] rounded-control px-5 text-sm gap-2",
};

/** Shared button primitive. Use for <button>; wrap in Link for navigation. */
export function Button({ variant = "primary", size = "md", leadingIcon, className, children, type = "button", ...rest }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center font-medium transition-colors duration-standard ease-standard select-none",
        "disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {leadingIcon}
      {children}
    </button>
  );
}
