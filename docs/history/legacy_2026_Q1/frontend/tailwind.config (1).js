/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        ic: {
          dark: '#050B14',
          slate: '#0A1628',
          cyan: '#00E5FF',
          blue: '#00A3FF',
          muted: '#64748B',
          white: '#F8FAFC',
        },
        primary: {
          DEFAULT: 'var(--color-primary)',
          dark: 'var(--color-primary-dark)',
        },
        surface: {
          bg: 'var(--color-surface-bg)',
          card: 'var(--color-surface-card)',
          border: 'var(--color-surface-border)',
          text: 'var(--color-surface-text)',
          muted: 'var(--color-surface-text-muted)',
        },
        neon: {
          cyan: '#00E5FF',
          green: '#00FF9D',
          blue: '#00A3FF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
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
          '0%, 100%': { transform: 'scale(1)', opacity: '0.5' },
          '50%': { transform: 'scale(1.1)', opacity: '1' },
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
      }
    },
  },
  plugins: [],
}
