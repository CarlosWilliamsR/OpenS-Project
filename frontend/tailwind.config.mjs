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
          100: '#f1f5f9',
          900: '#0f172a',
        }
      }
    },
  },
  plugins: [],
}
