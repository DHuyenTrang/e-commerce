import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: '#dedbd2',
        background: '#f6f4ef',
        foreground: '#17201b',
        primary: '#12634d',
        accent: '#9a5b18',
      },
      borderRadius: {
        DEFAULT: '6px',
      },
    },
  },
  plugins: [],
} satisfies Config
