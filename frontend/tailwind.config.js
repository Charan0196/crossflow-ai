export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { 
    extend: {
      colors: {
        'crossflow': {
          'bg': '#0a0f1a',
          'card': '#111827',
          'card-dark': '#0d1829',
          'border': '#1e3a5f',
          'nav': '#1a2942',
        }
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'spin-reverse': 'spin-reverse 2s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'bounce-slow': 'bounce 2s infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'spin-reverse': {
          '0%': { transform: 'rotate(360deg)' },
          '100%': { transform: 'rotate(0deg)' },
        },
        'glow': {
          '0%': { 
            boxShadow: '0 0 5px rgba(6, 182, 212, 0.5), 0 0 10px rgba(6, 182, 212, 0.3), 0 0 15px rgba(6, 182, 212, 0.2)' 
          },
          '100%': { 
            boxShadow: '0 0 10px rgba(139, 92, 246, 0.5), 0 0 20px rgba(139, 92, 246, 0.3), 0 0 30px rgba(139, 92, 246, 0.2)' 
          },
        }
      }
    } 
  },
  plugins: [],
}
