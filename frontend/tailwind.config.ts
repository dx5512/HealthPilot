import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: "#0078FF",
        "primary-dark": "#005EC4",
        danger: "#EF4444",
        warning: "#F59E0B",
        success: "#22C55E",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
