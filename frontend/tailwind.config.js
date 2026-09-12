/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // supports a dark mode
  theme: {
    extend: {
      colors: {
        // We can define custom premium dark theme colors here
        brand: {
          dark: "#0b0f19",
          card: "#161b26",
          border: "#262d3d",
          accent: "#3b82f6",
        }
      }
    },
  },
  plugins: [],
}
