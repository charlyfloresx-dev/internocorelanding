/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/**/*.{html,ts}',
    './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      colors: {
        'ic-dark': 'rgb(var(--color-ic-dark) / <alpha-value>)',
        'ic-slate': 'rgb(var(--color-ic-slate) / <alpha-value>)',
        'ic-cyan': 'rgb(var(--color-ic-cyan) / <alpha-value>)',
        'ic-blue': 'rgb(var(--color-ic-blue) / <alpha-value>)',
        'ic-muted': 'rgb(var(--color-ic-muted) / <alpha-value>)',
        'ic-white': 'rgb(var(--color-ic-white) / <alpha-value>)',

        primary: {
          DEFAULT: 'rgb(var(--color-primary) / <alpha-value>)',
          dark: 'rgb(var(--color-primary-dark) / <alpha-value>)',
          "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe", "300": "#93c5fd",
          "400": "#60a5fa", "500": "#3b82f6", "600": "#2563eb", "700": "#1d4ed8",
          "800": "#1e40af", "900": "#1e3a8a", "950": "#172554",
        },

        surface: {
          bg: 'rgb(var(--color-surface-bg) / <alpha-value>)',
          card: 'rgb(var(--color-surface-card) / <alpha-value>)',
          border: 'rgb(var(--color-surface-border) / <alpha-value>)',
          text: 'rgb(var(--color-surface-text) / <alpha-value>)',
          'text-muted': 'rgb(var(--color-surface-text-muted) / <alpha-value>)',
        },
        'nav-bar': 'rgb(var(--color-nav-bar) / <alpha-value>)',
        'nav-panel': 'rgb(var(--color-nav-panel) / <alpha-value>)',

        neon: {
          cyan: 'rgb(var(--color-neon-cyan) / <alpha-value>)',
          green: 'rgb(var(--color-neon-green) / <alpha-value>)',
          blue: 'rgb(var(--color-neon-blue) / <alpha-value>)',
        }
      },
      backdropBlur: {
        'xs': '2px',
        'industrial': '12px',
      },
      animation: {
        'spin-slow': 'spin 8s linear infinite',
        'shake': 'shake 0.2s ease-in-out 0s 2',
        'slide-in-right': 'slide-in-right 0.5s cubic-bezier(0.22, 1, 0.36, 1)',
        'gear-spin': 'gear-spin 2s linear infinite',
        'pulse-hexagon': 'pulse-hexagon 2s ease-in-out infinite',
        'bounce-x': 'bounce-x 1s infinite',
        'ping-horizontal': 'ping-horizontal 2s linear infinite',
        'scan-line': 'scan-line 2s linear infinite',
        'pulse-glow': 'pulse-glow 2s infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
        'fade-in-down': 'fade-in-down 0.5s ease-out',
      },
      keyframes: {
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-5px)' },
          '75%': { transform: 'translateX(5px)' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(100%)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'gear-spin': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        'pulse-hexagon': {
          '0%': { transform: 'scale(1)', opacity: '0.5' },
          '50%': { transform: 'scale(1.1)', opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '0.5' },
        },
        'bounce-x': {
          '0%, 100%': { transform: 'translateX(0)' },
          '50%': { transform: 'translateX(5px)' },
        },
        'ping-horizontal': {
          '0%': { transform: 'translateX(0)', opacity: '1' },
          '100%': { transform: 'translateX(300px)', opacity: '0' },
        },
        'scan-line': {
          '0%': { top: '0' },
          '100%': { top: '100%' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in-down': {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
};