/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      animation: {
        'blink-purple': 'blink-purple 1.5s ease-in-out infinite',
      },
      keyframes: {
        'blink-purple': {
          '0%, 100%': { 
            opacity: '1', 
            boxShadow: '0 0 15px rgba(168, 85, 247, 0.6), 0 0 30px rgba(168, 85, 247, 0.4)' 
          },
          '50%': { 
            opacity: '0.7', 
            boxShadow: '0 0 25px rgba(168, 85, 247, 0.9), 0 0 50px rgba(168, 85, 247, 0.6)' 
          },
        },
      },
    },
  },
  plugins: [],
}


