/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#121212',
        surfaceHover: '#1a1a1a',
        border: '#2a2a2a',
        primary: '#00e5ff',
        primaryHover: '#00b8cc',
        text: '#f3f4f6',
        textMuted: '#9ca3af',
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

