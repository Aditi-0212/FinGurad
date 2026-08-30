/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          bg: '#0B0F14',
          surface: '#131920',
          surface2: '#1A222B',
          border: '#232C36',
        },
        ink: {
          primary: '#E6EAEE',
          muted: '#8B96A3',
          faint: '#5B6572',
        },
        accent: {
          DEFAULT: '#2DD4BF',
          dim: '#1F9C8C',
          soft: 'rgba(45,212,191,0.12)',
        },
        risk: {
          low: '#34D399',
          medium: '#F59E0B',
          high: '#F87171',
        },
      },
      fontFamily: {
        display: ['"IBM Plex Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}