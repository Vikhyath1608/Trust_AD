/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // 'font-display' and 'font-body' used in JSX classNames
        display: ['"Syne"', 'sans-serif'],
        body:    ['"DM Sans"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        canvas: '#07070d',
        ink: {
          1: '#0c0c16',
          2: '#11111e',
          3: '#161626',
          4: '#1c1c30',
          5: '#23233a',   // ink-5 used in score-track etc.
        },
        edge: {
          1: 'rgba(255,255,255,0.05)',
          2: 'rgba(255,255,255,0.09)',
          3: 'rgba(255,255,255,0.16)',  // edge-3
        },
        word: {
          1: '#eeeef6',
          2: '#8888a8',
          3: '#4e4e6a',
        },
        violet: {
          300: '#c4b5fd', 400: '#a78bfa',
          500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9',
        },
        jade: { 400: '#34d399', 500: '#10b981' },
        coral:{ 400: '#f87171', 500: '#ef4444' },
        sun:  {
          300: '#fcd34d',  // sun-300
          400: '#fbbf24',
          500: '#f59e0b',  // sun-500
        },
        sky:  { 400: '#38bdf8', 500: '#0ea5e9' },
        pink: { 400: '#f472b6', 500: '#ec4899' },
      },
      animation: {
        'fade-up':    'fadeUp 0.45s cubic-bezier(0.16,1,0.3,1) forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'scale-in':   'scaleIn 0.35s cubic-bezier(0.16,1,0.3,1) forwards',
        'shimmer':    'shimmer 2s linear infinite',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'flow':       'flow 1.8s ease-in-out infinite',
      },
      keyframes: {
        fadeUp:    { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'none' } },
        fadeIn:    { from: { opacity: '0' }, to: { opacity: '1' } },
        scaleIn:   { from: { opacity: '0', transform: 'scale(0.95)' }, to: { opacity: '1', transform: 'scale(1)' } },
        shimmer:   { from: { backgroundPosition: '-600px 0' }, to: { backgroundPosition: '600px 0' } },
        pulseGlow: {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(139,92,246,0)' },
          '50%':     { boxShadow: '0 0 20px 6px rgba(139,92,246,0.25)' },
        },
        flow: {
          '0%,100%': { opacity: '0.3', transform: 'scaleX(0.95)' },
          '50%':     { opacity: '1',   transform: 'scaleX(1)' },
        },
      },
      boxShadow: {
        'glow-v': '0 0 30px rgba(139,92,246,0.35)',
        'glow-j': '0 0 24px rgba(52,211,153,0.3)',
        'glow-s': '0 0 24px rgba(251,191,36,0.3)',
        'card':   '0 4px 32px rgba(0,0,0,0.5)',
        'float':  '0 12px 48px rgba(0,0,0,0.7)',
      },
    },
  },
  plugins: [],
};
