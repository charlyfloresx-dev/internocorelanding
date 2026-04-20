/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#121212',
        'brand-surface': '#1F1F1F',
        'brand-primary': '#E2B714', // Dorado
        'brand-success': '#4ADE80', // Verde aprobación
        'brand-danger': '#F87171',  // Rojo descarte
      }
    },
  },
  plugins: [],
}
