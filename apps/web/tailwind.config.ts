import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        terracotta: {
          50: "#FDF6F5",
          100: "#F8EBE8",
          200: "#EED1CB",
          500: "#A75342",
          600: "#874436",
          700: "#6E362A",
        },
        ochre: {
          50: "#FEF7ED",
          100: "#FDEED3",
          500: "#E17709",
          600: "#C66506",
        },
        carbon: "#1B1B1B",
        graphite: "#4F4F4F",
        umber: "#4F4133",
        heritage: {
          50: "#F0F3FA",
          100: "#DFE6F5",
          500: "#455CA1",
          600: "#394C86",
        },
        sand: {
          50: "#FAF8F5",
          100: "#F3EFEA",
          200: "#E6DFD5",
          300: "#D5CABE",
          400: "#B8A99A",
          500: "#968676",
        },
        brand: {
          50: "#F8EBE8",
          100: "#EED1CB",
          500: "#A75342",
          600: "#874436",
          700: "#6E362A",
        },
      },
      fontFamily: {
        sans: ["var(--font-urbanist)", "Urbanist", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        urbanist: ["var(--font-urbanist)", "Urbanist", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
