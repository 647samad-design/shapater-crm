import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mist: "#EDF0F2", ink: "#16222E", muted: "#5E6B78", line: "#D5DBE1",
        pine: { DEFAULT: "#0F4C45", dark: "#0A3631", soft: "#DCEBE8" },
        brass: "#B07B1E", danger: "#B3412E",
      },
      fontFamily: { sans: ['"Schibsted Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
} satisfies Config;
