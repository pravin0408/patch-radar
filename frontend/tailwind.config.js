/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        severity: {
          critical: "#dc2626",
          high: "#ea580c",
          medium: "#ca8a04",
          low: "#6b7280",
        },
      },
    },
  },
  plugins: [],
};
