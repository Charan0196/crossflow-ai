// CrossFlow Logo Component
const CrossFlowLogo = ({ size = 'md', showText = true }) => {
  const sizes = { sm: 32, md: 44, lg: 64 };
  const s = sizes[size];
  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        <svg width={s} height={s} viewBox="0 0 64 64" fill="none">
          <defs>
            <linearGradient id="logoGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#059669" />
              <stop offset="100%" stopColor="#047857" />
            </linearGradient>
            <linearGradient id="logoGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#34d399" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#logoGrad1)" filter="url(#glow)"/>
          <path d="M20 32 L32 20 L44 32 L32 44 Z" fill="none" stroke="white" strokeWidth="2.5" strokeLinejoin="round"/>
          <path d="M26 32 L32 26 L38 32 L32 38 Z" fill="white" opacity="0.9"/>
          <circle cx="32" cy="16" r="3" fill="#34d399"/>
          <circle cx="48" cy="32" r="3" fill="#34d399"/>
          <circle cx="32" cy="48" r="3" fill="#34d399"/>
          <circle cx="16" cy="32" r="3" fill="#34d399"/>
          <path d="M32 16 L32 20" stroke="#34d399" strokeWidth="2"/>
          <path d="M48 32 L44 32" stroke="#34d399" strokeWidth="2"/>
          <path d="M32 48 L32 44" stroke="#34d399" strokeWidth="2"/>
          <path d="M16 32 L20 32" stroke="#34d399" strokeWidth="2"/>
        </svg>
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
      </div>
      {showText && (
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 via-green-400 to-teal-400 bg-clip-text text-transparent">
            CrossFlow
          </h1>
          <p className="text-[10px] text-emerald-500/70 font-medium tracking-wider">AI TRADING</p>
        </div>
      )}
    </div>
  );
};

export default CrossFlowLogo;
