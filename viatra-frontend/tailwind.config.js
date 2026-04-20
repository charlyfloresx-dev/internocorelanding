/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'obsidian': '#111319',
        'slate-hud': '#1d1f26',
        'cyan-neon': '#06b6d4',
        'amber-alert': '#f59e0b',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
        'mono': ['Space Grotesk', 'monospace'],
      },
       backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
