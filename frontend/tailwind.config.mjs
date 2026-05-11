/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        technical: {
          50: '#f8fafc',
          100: '#E2E8F0', // Gris clínico
          900: '#1E293B', // Deep Slate
        },
        primary: {
          DEFAULT: '#0052FF', // Azul Eléctrico
          hover: '#003ecc'
        }
      }
    },
  },
  plugins: [],
}
