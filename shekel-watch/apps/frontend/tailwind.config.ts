import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0f1117',
        panel:   '#1a1d2e',
        border:  '#2a2d3e',
        accent:  '#3b82f6',
        bull:    '#22c55e',
        bear:    '#ef4444',
        gold:    '#f59e0b',
        muted:   '#6b7280',
      },
      fontFamily: {
        sans:   ['Inter', 'sans-serif'],
        hebrew: ['Heebo', 'sans-serif'],
        mono:   ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config;
