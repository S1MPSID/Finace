import type { Config } from "tailwindcss";
import { ACCENT_DEEP_RGB, ACCENT_HEX, ACCENT_RGB } from "./lib/theme/colors";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#090d0d",
        panel: "#101716",
        mist: "#eef2ef",
        accent: ACCENT_HEX,
        emerald: "#15803d",
        line: "rgba(255,255,255,0.09)",
      },
      boxShadow: {
        glow: `0 20px 80px rgba(${ACCENT_RGB}, 0.2)`,
      },
      backgroundImage: {
        dots: `radial-gradient(circle at center, rgba(${ACCENT_RGB}, 0.28) 0, rgba(${ACCENT_RGB}, 0.28) 1px, transparent 1px)`,
      },
    },
  },
  plugins: [],
};

export default config;
