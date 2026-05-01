import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211b",
        muted: "#68736b",
        line: "#ded8ca",
        paper: "#fbf7ec",
        panel: "#fffdf7",
        moss: "#314c38",
        accent: "#0f766e",
        gain: "#9f1239",
        loss: "#047857"
      },
      boxShadow: {
        soft: "0 18px 50px rgba(41, 35, 24, 0.09)",
        card: "0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 18px 42px rgba(41, 35, 24, 0.08)"
      }
    }
  },
  plugins: []
} satisfies Config;
