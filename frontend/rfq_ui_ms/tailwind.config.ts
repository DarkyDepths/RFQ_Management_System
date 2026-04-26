import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
    "./src/utils/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        steel: {
          50: "#EEF4FB",
          100: "#D7E5F4",
          200: "#B3CDEA",
          300: "#85AEDB",
          400: "#5E94CB",
          500: "#3F7CB8",
          600: "#2F6093",
          700: "#244A72",
          800: "#1B3856",
          900: "#13283D",
        },
        gold: {
          100: "#F2E2B7",
          200: "#E5CD86",
          300: "#D5B25A",
          400: "#C49A3A",
          500: "#A8842D",
          600: "#856823",
          700: "#65501B",
        },
      },
      fontFamily: {
        sans: ["var(--font-body)", ...defaultTheme.fontFamily.sans],
        display: ["var(--font-display)", ...defaultTheme.fontFamily.sans],
        mono: ["var(--font-mono)", ...defaultTheme.fontFamily.mono],
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      boxShadow: {
        diffusion:
          "0 1px 0 hsl(220 14% 100% / 0.6) inset, 0 20px 48px -20px hsl(220 30% 20% / 0.10)",
        "diffusion-dark":
          "0 1px 0 hsl(0 0% 100% / 0.05) inset, 0 32px 64px -28px hsl(0 0% 0% / 0.6)",
        glow: "0 0 0 1px hsl(0 0% 100% / 0.06), 0 16px 48px hsl(0 0% 0% / 0.25)",
        steel: "0 12px 32px -8px hsl(215 70% 30% / 0.18)",
        gold: "0 12px 32px -8px hsl(36 70% 40% / 0.12)",
        "inner-edge": "inset 0 1px 0 hsl(0 0% 100% / 0.08)",
      },
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        pulseRing: {
          "0%, 100%": { opacity: "0.35", transform: "scale(1)" },
          "50%": { opacity: "0.65", transform: "scale(1.04)" },
        },
        lift: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        breathe: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-3px)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        pulseRing: "pulseRing 2.4s ease-in-out infinite",
        lift: "lift 380ms cubic-bezier(0.16, 1, 0.3, 1)",
        fadeIn: "fadeIn 280ms ease-out",
        breathe: "breathe 2.6s ease-in-out infinite",
        float: "float 4s ease-in-out infinite",
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
