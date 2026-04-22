import React from 'react'
import { TrendingUp, Zap, ArrowRight, Brain, Cpu, Network } from 'lucide-react'

// Enhanced CrossFlow AI Logo Component - Simplified and Fixed
const CrossFlowLogo = ({ size = 'medium', showText = false, animated = true }) => {
  const sizes = {
    small: { container: 'w-8 h-8', text: 'text-sm' },
    medium: { container: 'w-12 h-12', text: 'text-xl' },
    large: { container: 'w-16 h-16', text: 'text-2xl' },
    xl: { container: 'w-24 h-24', text: 'text-4xl' },
    xxl: { container: 'w-32 h-32', text: 'text-5xl' }
  }

  const currentSize = sizes[size]

  return (
    <div className="flex items-center space-x-3">
      {/* Simplified Logo Icon */}
      <div className={`${currentSize.container} relative flex items-center justify-center`}>
        {/* Outer Ring with Animation */}
        <div className={`${currentSize.container} absolute inset-0 rounded-full border-2 border-cyan-400 ${animated ? 'animate-spin-slow' : ''} opacity-60`}></div>
        
        {/* Inner Background */}
        <div className={`${currentSize.container} relative bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-full flex items-center justify-center shadow-xl border border-cyan-400/30`}>
          {/* CrossFlow Symbol */}
          <div className="relative">
            {/* Cross Pattern */}
            <div className="w-6 h-1 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
            <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
            
            {/* Center AI Dot */}
            <div className="w-3 h-3 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
              <div className={`w-1 h-1 bg-white rounded-full ${animated ? 'animate-pulse' : ''}`}></div>
            </div>
            
            {/* Corner Dots */}
            <div className="w-1 h-1 bg-cyan-400 rounded-full absolute -top-2 -left-2"></div>
            <div className="w-1 h-1 bg-purple-500 rounded-full absolute -top-2 -right-2"></div>
            <div className="w-1 h-1 bg-pink-500 rounded-full absolute -bottom-2 -left-2"></div>
            <div className="w-1 h-1 bg-orange-500 rounded-full absolute -bottom-2 -right-2"></div>
          </div>
        </div>
        
        {/* Glow Effect */}
        {animated && (
          <div className={`${currentSize.container} absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-purple-500/20 rounded-full blur-md animate-pulse`}></div>
        )}
      </div>

      {/* Logo Text */}
      <div className="flex flex-col">
        <div className="flex items-center space-x-2">
          <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
            CrossFlow
          </span>
          <span className="text-lg font-bold text-cyan-400">AI</span>
        </div>
        {showText && (
          <div className="text-xs text-slate-400 font-medium tracking-wider uppercase">
            Cross-Chain DeFi Trading
          </div>
        )}
      </div>
    </div>
  )
}

// Simplified Compact Logo
const CompactLogo = ({ animated = true }) => {
  return (
    <div className="flex items-center space-x-2">
      <div className="w-8 h-8 relative flex items-center justify-center">
        {/* Animated Border Ring */}
        <div className={`w-8 h-8 absolute inset-0 rounded-lg border-2 border-cyan-400 ${animated ? 'animate-pulse' : ''}`}></div>
        
        {/* Inner Content */}
        <div className="w-8 h-8 bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-lg flex items-center justify-center relative">
          {/* Simple Cross Pattern */}
          <div className="relative">
            <div className="w-4 h-0.5 bg-gradient-to-r from-cyan-400 to-purple-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full"></div>
            <div className="w-0.5 h-4 bg-gradient-to-b from-purple-500 to-pink-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full"></div>
            <div className="w-1.5 h-1.5 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
              <div className={`w-0.5 h-0.5 bg-white rounded-full ${animated ? 'animate-pulse' : ''}`}></div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-1">
        <span className="text-sm font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
          CF
        </span>
        <Brain className="w-3 h-3 text-cyan-400" />
      </div>
    </div>
  )
}

// Simplified Loading Logo Animation
const LoadingLogo = () => {
  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="w-20 h-20 relative">
        {/* Rotating Rings */}
        <div className="w-20 h-20 absolute inset-0 border-4 border-transparent border-t-cyan-400 border-r-purple-500 rounded-full animate-spin"></div>
        <div className="w-16 h-16 absolute inset-2 border-3 border-transparent border-b-pink-400 border-l-orange-400 rounded-full animate-spin" style={{ animationDirection: 'reverse' }}></div>
        
        {/* Center Logo */}
        <div className="w-12 h-12 absolute inset-4 bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-full flex items-center justify-center border border-cyan-400/50">
          <div className="relative">
            <Brain className="w-6 h-6 text-cyan-400 animate-pulse" />
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-purple-400 rounded-full animate-ping"></div>
          </div>
        </div>
      </div>
      
      <div className="text-center">
        <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-2">
          CrossFlow AI
        </div>
        <div className="text-sm text-slate-400 animate-pulse mb-2">
          Initializing AI Trading Engine...
        </div>
        <div className="flex items-center justify-center space-x-2">
          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  )
}

export { CrossFlowLogo, CompactLogo, LoadingLogo }
export default CrossFlowLogo