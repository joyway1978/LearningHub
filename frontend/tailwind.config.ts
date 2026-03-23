import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a1a2e',
          hover: '#2d2d44',
          50: '#f0f0f5',
          100: '#e1e1eb',
          200: '#c3c3d7',
          300: '#a5a5c3',
          400: '#8787af',
          500: '#69699b',
          600: '#4b4b87',
          700: '#2d2d44',
          800: '#1a1a2e',
          900: '#0d0d17',
        },
        accent: {
          DEFAULT: '#f59e0b',
          hover: '#d97706',
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        surface: {
          DEFAULT: '#ffffff',
          secondary: '#fafaf9',
        },
        background: {
          DEFAULT: '#fafaf9',
        },
        border: {
          DEFAULT: '#e7e5e4',
        },
        text: {
          primary: '#1c1917',
          secondary: '#78716c',
          muted: '#a8a29e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      borderRadius: {
        'sm': '4px',
        'md': '6px',
      },
    },
  },
  plugins: [],
};

export default config;
