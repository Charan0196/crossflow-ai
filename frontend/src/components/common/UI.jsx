import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

// Dark gradient background with subtle cyan/green tint
export const AnimatedBackground = () => (
  <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
    <div 
      className="absolute inset-0" 
      style={{ backgroundColor: '#0c1222' }}
    />
  </div>
);

// Glass Card - matching the reference image style
export const GlassCard = ({ children, className = '', glow = false, padding = 'p-5' }) => (
  <div 
    className={`relative backdrop-blur-xl rounded-2xl ${padding} ${className}`}
    style={{
      backgroundColor: 'rgba(17, 24, 39, 0.8)',
      border: glow ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid rgba(30, 58, 95, 0.5)',
      boxShadow: glow ? '0 0 30px -5px rgba(6, 182, 212, 0.15)' : 'none'
    }}
  >
    {children}
  </div>
);

// Glow Button - cyan accent style
export const GlowButton = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  icon: Icon, 
  onClick, 
  className = '', 
  disabled = false, 
  type = 'button' 
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          background: 'linear-gradient(to right, #06b6d4, #10b981)',
          color: '#000',
          fontWeight: 600,
          boxShadow: '0 4px 15px rgba(6, 182, 212, 0.2)'
        };
      case 'secondary':
        return {
          backgroundColor: '#1a2942',
          color: '#fff',
          border: '1px solid rgba(42, 74, 106, 0.5)'
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          border: '2px solid rgba(6, 182, 212, 0.5)',
          color: '#22d3ee'
        };
      case 'ghost':
        return {
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          color: '#22d3ee'
        };
      case 'danger':
        return {
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          color: '#f87171',
          border: '1px solid rgba(239, 68, 68, 0.3)'
        };
      default:
        return {};
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm': return { padding: '6px 12px', fontSize: '12px', gap: '6px', borderRadius: '8px' };
      case 'md': return { padding: '10px 16px', fontSize: '14px', gap: '8px', borderRadius: '12px' };
      case 'lg': return { padding: '12px 24px', fontSize: '16px', gap: '10px', borderRadius: '12px' };
      case 'xl': return { padding: '16px 32px', fontSize: '18px', gap: '12px', borderRadius: '16px' };
      default: return {};
    }
  };

  const iconSize = size === 'sm' ? 14 : size === 'lg' ? 20 : 16;

  return (
    <button 
      type={type}
      onClick={onClick} 
      disabled={disabled}
      className={`inline-flex items-center justify-center font-medium transition-all duration-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      style={{ ...getVariantStyles(), ...getSizeStyles() }}
    >
      {Icon && <Icon size={iconSize} />}
      {children}
    </button>
  );
};

// Icon Button
export const IconButton = ({ icon: Icon, variant = 'ghost', size = 'md', onClick, badge, className = '' }) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'ghost':
        return {
          backgroundColor: 'rgba(26, 41, 66, 0.5)',
          color: '#9ca3af',
          border: '1px solid rgba(42, 74, 106, 0.3)'
        };
      case 'primary':
        return {
          backgroundColor: 'rgba(6, 182, 212, 0.2)',
          color: '#22d3ee',
          border: '1px solid rgba(6, 182, 212, 0.3)'
        };
      case 'danger':
        return {
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          color: '#f87171'
        };
      default:
        return {};
    }
  };

  const sizes = { sm: '6px', md: '10px', lg: '12px' };
  const iconSizes = { sm: 14, md: 18, lg: 22 };

  return (
    <button 
      onClick={onClick} 
      className={`relative rounded-xl transition-all duration-200 hover:opacity-80 ${className}`}
      style={{ ...getVariantStyles(), padding: sizes[size] }}
    >
      <Icon size={iconSizes[size]} />
      {badge && (
        <span 
          className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-black flex items-center justify-center"
          style={{ backgroundColor: '#06b6d4', fontSize: '10px', fontWeight: 'bold' }}
        >
          {badge}
        </span>
      )}
    </button>
  );
};

// Status Badge - cyan/green style
export const StatusBadge = ({ status, label }) => {
  const getStyles = () => {
    switch (status) {
      case 'active':
        return { bg: 'rgba(16, 185, 129, 0.2)', color: '#34d399', border: 'rgba(16, 185, 129, 0.4)', dot: '#34d399' };
      case 'warning':
        return { bg: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)', dot: '#fbbf24' };
      case 'error':
        return { bg: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: 'rgba(239, 68, 68, 0.4)', dot: '#f87171' };
      case 'info':
      default:
        return { bg: 'rgba(6, 182, 212, 0.2)', color: '#22d3ee', border: 'rgba(6, 182, 212, 0.4)', dot: '#22d3ee' };
    }
  };

  const styles = getStyles();

  return (
    <span 
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
      style={{ backgroundColor: styles.bg, color: styles.color, border: `1px solid ${styles.border}` }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: styles.dot }} />
      {label}
    </span>
  );
};

// Metric Card - clean style matching image
export const MetricCard = ({ icon: Icon, label, value, change, color = 'cyan', subtitle }) => {
  const getColorStyles = () => {
    switch (color) {
      case 'cyan': return { text: '#22d3ee', bg: 'rgba(6, 182, 212, 0.1)', border: 'rgba(6, 182, 212, 0.2)' };
      case 'emerald': return { text: '#34d399', bg: 'rgba(16, 185, 129, 0.1)', border: 'rgba(16, 185, 129, 0.2)' };
      case 'purple': return { text: '#a78bfa', bg: 'rgba(139, 92, 246, 0.1)', border: 'rgba(139, 92, 246, 0.2)' };
      case 'amber': return { text: '#fbbf24', bg: 'rgba(245, 158, 11, 0.1)', border: 'rgba(245, 158, 11, 0.2)' };
      default: return { text: '#22d3ee', bg: 'rgba(6, 182, 212, 0.1)', border: 'rgba(6, 182, 212, 0.2)' };
    }
  };

  const colorStyles = getColorStyles();

  return (
    <GlassCard padding="p-4">
      <div className="flex items-start justify-between mb-3">
        <div 
          className="p-2.5 rounded-xl"
          style={{ backgroundColor: colorStyles.bg, border: `1px solid ${colorStyles.border}` }}
        >
          <Icon size={18} style={{ color: colorStyles.text }} />
        </div>
        {change !== undefined && (
          <div 
            className="flex items-center gap-1 text-xs font-semibold"
            style={{ color: change >= 0 ? '#34d399' : '#f87171' }}
          >
            {change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
      <p className="text-xs mb-1" style={{ color: '#9ca3af' }}>{label}</p>
      <p className="text-xl font-bold" style={{ color: colorStyles.text }}>{value}</p>
      {subtitle && <p className="text-xs mt-1" style={{ color: '#6b7280' }}>{subtitle}</p>}
    </GlassCard>
  );
};

// Stat Box - for inline stats like in the image
export const StatBox = ({ label, value, color = 'cyan' }) => {
  const getColor = () => {
    switch (color) {
      case 'cyan': return '#22d3ee';
      case 'emerald': return '#34d399';
      case 'white': return '#ffffff';
      default: return '#22d3ee';
    }
  };

  return (
    <div 
      className="text-center p-4 rounded-xl"
      style={{ 
        backgroundColor: 'rgba(17, 24, 39, 0.5)', 
        border: '1px solid rgba(30, 58, 95, 0.3)' 
      }}
    >
      <p className="text-xs mb-1" style={{ color: '#9ca3af' }}>{label}</p>
      <p className="text-lg font-bold" style={{ color: getColor() }}>{value}</p>
    </div>
  );
};
