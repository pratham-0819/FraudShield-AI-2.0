import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#07111F",
        card: "#0A1A2E",
        border: "#22314A",
        primary: "#38BDF8",
        status: {
          safe: "#22C55E",
          warning: "#FBBF24",
          fraud: "#EF4444",
        },
      },
      fontFamily: {
        sans: ["var(--font-display)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
