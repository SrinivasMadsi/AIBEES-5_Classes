/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        intake:     { 50: "#fefce8", 100: "#fef9c3", 600: "#ca8a04", 700: "#a16207" },
        validation: { 50: "#eff6ff", 100: "#dbeafe", 600: "#2563eb", 700: "#1d4ed8" },
        resolution: { 50: "#faf5ff", 100: "#f3e8ff", 600: "#9333ea", 700: "#7e22ce" },
      },
      fontFamily: {
        sans:    ['"Inter"', "system-ui", "sans-serif"],
        display: ['"Bricolage Grotesque"', '"Inter"', "sans-serif"],
        mono:    ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
