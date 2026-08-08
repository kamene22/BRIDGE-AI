import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: "#faf7f2",
          100: "#f6f3ee",
          200: "#eee8df",
          300: "#e4dacb",
          400: "#d6c5b0",
        },
        sand: {
          100: "#f3ede3",
          200: "#ede7dc",
          300: "#e6ded1",
          400: "#ded4c3",
          500: "#d3c6b2",
        },
        charcoal: {
          800: "#292524",
          900: "#1c1917",
          950: "#0c0a09",
        },
        terracotta: {
          500: "#e06d53",
          600: "#c85a32",
        }
      },
      fontFamily: {
        serif: ["Instrument Serif", "Georgia", "serif"],
        sans: ["Outfit", "Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
};
export default config;
