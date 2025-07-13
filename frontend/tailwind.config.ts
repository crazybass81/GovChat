import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        secondary: '#14B8A6',
        surface: '#FFFFFF',
        background: '#F9FAFB',
        text: '#111827',
        textMuted: '#6B7280',
        warning: '#F59E0B',
        error: '#DC2626'
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans KR', 'sans-serif']
      },
      spacing: {
        's0': '0px',
        's1': '4px',
        's2': '8px',
        's3': '16px',
        's4': '24px',
        's5': '32px'
      },
      borderRadius: {
        'small': '4px',
        'medium': '8px',
        'large': '12px'
      }
    },
  },
  plugins: [],
}
export default config