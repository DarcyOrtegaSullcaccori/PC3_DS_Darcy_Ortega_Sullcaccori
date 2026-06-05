/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        peru: {
          red: '#D91023',
          dark: '#9B0A17',
        },
      },
    },
  },
  plugins: [],
}
