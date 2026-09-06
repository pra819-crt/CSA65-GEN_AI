import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./context/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#f8fafc",
          900: "#ffffff",
          800: "#f1f5f9",
          700: "#e2e8f0",
          600: "#cbd5e1",
        },
        status: {
          nominal: "#059669",
          warning: "#d97706",
          critical: "#e11d48",
          reroute: "#0891b2",
          gold: "#b45309",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(15,23,42,0.06), 0 4px 16px rgba(15,23,42,0.06)",
        glow: "0 0 20px rgba(5,150,105,0.20)",
      },
      animation: {
        pulseSlow: "pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
