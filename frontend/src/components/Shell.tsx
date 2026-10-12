import type { ReactNode } from "react";

export const pill =
  "inline-flex items-center justify-center rounded-full bg-gradient-to-r from-[#0b1b3a] to-[#1e3a6e] px-7 py-3 text-[15px] font-semibold text-white aq-btn";
export const pillGhost =
  "inline-flex items-center justify-center rounded-full border-2 border-brand bg-surface px-7 py-3 text-[15px] font-semibold text-brand transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand hover:text-white active:translate-y-0 active:scale-[0.98]";
export const card =
  "page-in rounded-3xl border border-line bg-surface p-6 shadow-[0_8px_24px_rgba(11,27,58,0.06)] sm:p-8";
export const field =
  "w-full rounded-xl border border-line bg-surface px-4 py-3 text-base font-normal text-ink outline-none transition-colors focus:border-brand";

/** The Q of the wordmark, drawn as a QR corner square with a tail. */
export function QMark({
  size = 24,
  ink = "currentColor",
  gap = "#ffffff",
  className = "",
}: {
  size?: number;
  ink?: string;
  gap?: string;
  className?: string;
}) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className={className} aria-hidden="true">
      <rect
        x="12"
        y="12"
        width="68"
        height="68"
        rx="21"
        fill="none"
        stroke={ink}
        strokeWidth="15"
      />
      <rect x="36" y="36" width="20" height="20" rx="5" fill="var(--color-lime)" />
      <path d="M62 62 L90 90" stroke={gap} strokeWidth="26" strokeLinecap="round" />
      <path d="M64 64 L90 90" stroke="var(--color-lime)" strokeWidth="15" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <span
      role="img"
      aria-label="AuthentiQ"
      className={`inline-flex items-center text-[24px] leading-none font-extrabold tracking-[-0.04em] ${dark ? "text-white" : "text-ink"}`}
    >
      <span aria-hidden="true">Authenti</span>
      <QMark
        size={25}
        gap={dark ? "var(--color-ink)" : "#ffffff"}
        className="ml-[1.5px] translate-y-[2px]"
      />
    </span>
  );
}

/** Header and footer for the scan and manufacturer pages. */
export function Shell({ page, children }: { page: "scan" | "manufacturer"; children: ReactNode }) {
  const link = (href: string, text: string, active: boolean) => (
    <a
      href={href}
      aria-current={active ? "page" : undefined}
      className={`px-3 py-3 text-[15px] transition-colors hover:text-brand ${active ? "font-semibold text-brand" : ""}`}
    >
      {text}
    </a>
  );
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-soft via-surface to-surface">
      <header className="fixed inset-x-0 top-0 z-50">
        <div className="mx-auto flex h-24 max-w-[1180px] items-center justify-between gap-3 px-5">
          <a
            href="#/"
            aria-label="AuthentiQ home"
            className="rounded-full bg-surface/85 px-4 py-2 backdrop-blur"
          >
            <Logo />
          </a>
          <nav
            aria-label="Main"
            className="flex items-center rounded-full bg-surface px-3 shadow-[0_5px_14px_rgba(11,27,58,0.08)]"
          >
            <span className="hidden sm:block">{link("#/", "Home", false)}</span>
            {link("#/scan", "Scan", page === "scan")}
            {link("#/manufacturer", "Manufacturers", page === "manufacturer")}
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="border-t border-line px-5 py-8 text-center text-sm text-subtle">
        © AuthentiQ ·{" "}
        <a href="#contact" className="underline hover:text-brand">
          Contact us
        </a>
      </footer>
    </div>
  );
}
