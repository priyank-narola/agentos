import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}", "./lib/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // ── Product neutrals ────────────────────────────────────────────────
        canvas: "#f4f6f5", // app background (calm, faint green-grey)
        surface: "#ffffff", // primary card / elevated surface
        surfaceMuted: "#f5f7f6", // secondary fill (subtle wells, zebra)
        surfaceSunken: "#eef1f0", // inset wells / code blocks
        ink: "#101827", // primary text + dark (sidebar / authority surfaces)
        inkMuted: "#51606c", // secondary text
        inkSubtle: "#6c7886", // tertiary / meta text (still AA on white)
        inkFaint: "#a0a9b2", // placeholder / disabled / decorative-only text
        hairline: "#e5e8ea", // default hairline borders
        hairlineStrong: "#d4dadb", // emphasized hairlines (inputs, focus edges)

        // ── Brand signal (governance green) ─────────────────────────────────
        signal: "#2e7d68",
        signalHover: "#256e5b",
        signalSoft: "#e9f3ef",
        signalSoftBorder: "#d0e3da",
        signalText: "#ffffff",

        // ── Semantic status (calm, enterprise tones) ────────────────────────
        success: "#0f6d4f",
        successBg: "#e9f4ee",
        successBorder: "#cfe5d9",
        warning: "#8f5a07",
        warningBg: "#fbf4e3",
        warningBorder: "#ecd9ad",
        danger: "#b3261e",
        dangerBg: "#fdf0ee",
        dangerBorder: "#f2cfcb",
        info: "#1a56a0",
        infoBg: "#eef3fa",
        infoBorder: "#d3e1f2",
        neutral: "#51606c",
        neutralBg: "#f4f5f6",
        neutralBorder: "#e0e3e6",

        // ── Focus ───────────────────────────────────────────────────────────
        focusRing: "#1f6f5a",
        focusRingOnDark: "#7fd8c2",
      },
      borderRadius: {
        control: "6px", // inputs, buttons, small controls
        card: "8px", // cards / surfaces
        popover: "10px", // menus, tooltips, popovers
        dialog: "12px", // dialogs / modals
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 24, 39, 0.04), 0 1px 1px rgba(16, 24, 39, 0.03)",
        elevated: "0 6px 16px rgba(16, 24, 39, 0.08), 0 2px 4px rgba(16, 24, 39, 0.04)",
        dialog: "0 16px 40px rgba(16, 24, 39, 0.18), 0 2px 8px rgba(16, 24, 39, 0.08)",
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.2, 0, 0, 1)", // Apple-style standard ease
        emphasized: "cubic-bezier(0.16, 1, 0.3, 1)", // enter / exit emphasis
      },
      transitionDuration: {
        fast: "150ms",
        standard: "200ms",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Inter",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
