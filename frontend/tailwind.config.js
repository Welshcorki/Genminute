import colors from 'tailwindcss/colors'
import defaultTheme from 'tailwindcss/defaultTheme'

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 브랜드 액센트 — 로고/theme-color(#4f46e5)와 동일한 indigo 계열.
        // UI 액센트는 brand-* 만 사용. 다색은 화자 구분(src/config/speakers.ts)에만 허용.
        brand: colors.indigo,
      },
      fontFamily: {
        sans: ['"Pretendard Variable"', 'Pretendard', ...defaultTheme.fontFamily.sans],
      },
    },
  },
  plugins: [],
}
