"use client";

import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Wordmark, AppNav, NavLinksMobile } from "@/components/app-nav";
import { IdentityBar } from "@/components/identity-bar";
import { Status } from "@/components/ui/Status";

function SandboxIndicator() {
  return (
    <span className="hidden items-center gap-1.5 rounded-full border border-hairline bg-surface px-2.5 py-1 text-[11px] font-medium text-inkFaint md:inline-flex">
      <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-signal" />
      Sandbox
    </span>
  );
}

function TopBar() {
  const [open, setOpen] = useState(false);

  // Escape closes the drawer, and the page behind it must not scroll while
  // it is open — otherwise the underlying content moves under the overlay.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-hairline bg-surface/90 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-[1180px] items-center justify-between gap-3 px-5 lg:px-8">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setOpen(true)}
              aria-label="Open menu"
              aria-expanded={open}
              className="grid h-9 w-9 place-items-center rounded-control text-ink hover:bg-surfaceMuted lg:hidden"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
                <path d="M2.5 5h13M2.5 9h13M2.5 13h13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
            <Wordmark />
          </div>

          <AppNav className="hidden min-w-0 lg:flex" />

          <div className="flex items-center gap-2.5">
            <SandboxIndicator />
            <IdentityBar />
          </div>
        </div>
      </header>

      {/* Rendered as a sibling of <header>, never inside it: the header's
          backdrop-blur establishes a containing block for fixed-position
          descendants, which would clip this drawer to the header's height. */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div aria-hidden className="absolute inset-0 bg-ink/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 flex w-[min(86vw,320px)] flex-col overflow-y-auto border-r border-hairline bg-surface px-4 py-4 shadow-elevated">
            <div className="flex items-center justify-between">
              <Wordmark />
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close menu"
                className="grid h-9 w-9 place-items-center rounded-control text-inkSubtle hover:bg-surfaceMuted"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path d="m3.5 3.5 9 9m0-9-9 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <nav className="mt-2 flex-1 pb-6" aria-label="Mobile navigation">
              <NavLinksMobile onNavigate={() => setOpen(false)} />
            </nav>
          </div>
        </div>
      )}
    </>
  );
}

export function RegistryShell({
  children,
  title,
  eyebrow,
  actions,
}: {
  children: ReactNode;
  title?: string;
  eyebrow?: string;
  /** primary page-level actions rendered at the header right */
  actions?: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-canvas">
      <TopBar />
      <main className="mx-auto w-full max-w-[1180px] px-5 py-7 lg:px-8 lg:py-9">
        {(title || eyebrow) && (
          <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
            <div className="min-w-0">
              {eyebrow && <p className="eyebrow text-inkFaint">{eyebrow}</p>}
              {title && <h1 className="mt-1.5 text-[28px] font-semibold leading-tight tracking-tight text-ink lg:text-[32px]">{title}</h1>}
            </div>
            {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
          </div>
        )}
        {children}
      </main>
      <footer className="mx-auto w-full max-w-[1180px] px-5 pb-10 lg:px-8">
        <p className="border-t border-hairline pt-4 text-[11px] text-inkFaint">AgentOS — sandbox demonstration environment. No real money movement. All executions run in the AgentOS sandbox provider.</p>
      </footer>
    </div>
  );
}

/** Legacy shared message (kept for existing screens). */
export function StateMessage({ children, tone = "muted" }: { children: ReactNode; tone?: "muted" | "error" }) {
  if (tone === "error") {
    return (
      <div role="alert" className="rounded-card border border-dangerBorder bg-dangerBg px-5 py-4 text-sm text-danger">
        {children}
      </div>
    );
  }
  return <div className={cn("rounded-card border border-dashed border-hairlineStrong bg-surface px-5 py-4 text-sm text-inkSubtle")}>{children}</div>;
}

/** Legacy status chip (kept for existing screens) — delegates to canonical Status. */
export function StatusPill({ value, className }: { value: string; className?: string }) {
  return <Status value={value} className={className} />;
}
