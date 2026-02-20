/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0A4F70',      // Core Blue
        secondary: '#B0B7C0',    // Steel Gray
        accent: '#32CD32',       // Cyber Green
        'industrial-dark': '#1A1D24',
        'industrial-gray': {
          DEFAULT: '#2A2F3A',
          light: '#3B4252',
          dark: '#1F232B'
        }
      },
    },
  },
  plugins: [],
}