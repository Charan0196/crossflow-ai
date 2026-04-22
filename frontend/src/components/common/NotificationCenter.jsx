/**
 * Phase 5: Enhanced Notification Center Component
 * 
 * Professional notifications with:
 * - Glassmorphism effects
 * - Smooth animations
 * - Toast notifications
 * - Notification history
 */

import { useState, useEffect } from 'react';
import { Bell, X, Check, TrendingUp, Wallet, Brain, Shield, Sparkles, Zap, AlertTriangle } from 'lucide-react';
import { useAccount } from 'wagmi';

const NotificationIcon = ({ type }) => {
  const icons = {
    transaction_status: { icon: Wallet, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    order_filled: { icon: Check, color: 'text-green-400', bg: 'bg-green-500/20' },
    price_alert: { icon: TrendingUp, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    ai_signal: { icon: Brain, color: 'text-[#2dd4bf]', bg: 'bg-[#2dd4bf]/20' },
    security_warning: { icon: Shield, color: 'text-red-400', bg: 'bg-red-500/20' },
    default: { icon: Bell, color: 'text-gray-400', bg: 'bg-gray-500/20' }
  };
  
  const config = icons[type] || icons.default;
  const Icon = config.icon;
  
  return (
    <div className={`p-2 rounded-xl ${config.bg}`}>
      <Icon size={16} className={config.color} />
    </div>
  );
};

const NotificationToast = ({ notification, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const priorityStyles = {
    urgent: 'border-red-500/50 bg-gradient-to-r from-red-500/20 to-red-500/5 shadow-red-500/20',
    high: 'border-yellow-500/50 bg-gradient-to-r from-yellow-500/20 to-yellow-500/5 shadow-yellow-500/20',
    medium: 'border-[#2dd4bf]/50 bg-gradient-to-r from-[#2dd4bf]/20 to-[#2dd4bf]/5 shadow-[#2dd4bf]/20',
    low: 'border-gray-500/50 bg-gradient-to-r from-gray-500/20 to-gray-500/5 shadow-gray-500/20'
  };

  return (
    <div className={`p-4 rounded-2xl border backdrop-blur-xl shadow-xl animate-slide-in-right ${priorityStyles[notification.priority] || priorityStyles.medium}`}>
      <div className="flex items-start gap-3">
        <NotificationIcon type={notification.type} />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-white text-sm">{notification.title}</p>
          <p className="text-xs text-gray-400 mt-1 line-clamp-2">{notification.message}</p>
        </div>
        <button 
          onClick={onClose} 
          className="p-1.5 rounded-lg hover:bg-white/10 text-gray-500 hover:text-white transition-colors"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
};

const NotificationCenter = () => {
  const { address } = useAccount();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Add demo notification on mount for testing
  useEffect(() => {
    if (address) {
      const welcomeNotification = {
        id: 'welcome-' + Date.now(),
        type: 'ai_signal',
        title: 'Welcome to CrossFlow AI',
        message: 'Your wallet is connected. AI signals are now active and monitoring the market.',
        priority: 'medium',
        timestamp: new Date().toISOString(),
        read: false
      };
      setNotifications([welcomeNotification]);
      setUnreadCount(1);
    }
  }, [address]);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const markAsRead = (id) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ));
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  return (
    <>
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-[200] space-y-3 w-96">
        {toasts.map(toast => (
          <NotificationToast 
            key={toast.id} 
            notification={toast} 
            onClose={() => removeToast(toast.id)} 
          />
        ))}
      </div>

      {/* Notification Bell - Fixed Position */}
      <div className="fixed bottom-6 right-6 z-[100]">
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className={`relative p-4 rounded-2xl transition-all duration-300 shadow-xl ${
            isOpen 
              ? 'bg-gradient-to-br from-[#2dd4bf] to-[#06b6d4] shadow-[#2dd4bf]/30' 
              : 'bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] border border-[#2a3441] hover:border-[#2dd4bf]/50 hover:shadow-[#2dd4bf]/20'
          }`}
        >
          <Bell size={24} className={isOpen ? 'text-black' : 'text-gray-400'} />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-lg shadow-red-500/50 animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Dropdown Panel */}
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            <div className="absolute right-0 bottom-full mb-4 w-96 bg-gradient-to-b from-[#1a1f2e] to-[#0d1117] border border-[#2a3441] rounded-3xl shadow-2xl shadow-black/50 z-50 overflow-hidden animate-scale-in">
              {/* Header */}
              <div className="p-5 border-b border-[#2a3441] bg-[#1a1f2e]/80 backdrop-blur-xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-[#2dd4bf]/20">
                      <Bell size={18} className="text-[#2dd4bf]" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">Notifications</h3>
                      <p className="text-xs text-gray-500">{unreadCount} unread</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={markAllAsRead} 
                      className="px-3 py-1.5 rounded-lg text-xs font-medium text-[#2dd4bf] hover:bg-[#2dd4bf]/10 transition-colors"
                    >
                      Mark all read
                    </button>
                    <button 
                      onClick={clearAll} 
                      className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:text-white hover:bg-[#2a3441] transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </div>

              {/* Notifications List */}
              <div className="max-h-[400px] overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-12 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#2a3441]/50 flex items-center justify-center">
                      <Bell size={32} className="text-gray-600" />
                    </div>
                    <p className="text-gray-500 font-medium">No notifications</p>
                    <p className="text-xs text-gray-600 mt-1">You're all caught up!</p>
                  </div>
                ) : (
                  <div className="p-3 space-y-2">
                    {notifications.map((notification, index) => (
                      <div 
                        key={notification.id}
                        onClick={() => markAsRead(notification.id)}
                        style={{ animationDelay: `${index * 50}ms` }}
                        className={`p-4 rounded-2xl cursor-pointer transition-all duration-200 animate-slide-in-up ${
                          notification.read 
                            ? 'bg-transparent hover:bg-[#2a3441]/30' 
                            : 'bg-gradient-to-r from-[#2dd4bf]/10 to-transparent border border-[#2dd4bf]/20 hover:border-[#2dd4bf]/40'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <NotificationIcon type={notification.type} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className={`text-sm font-semibold ${notification.read ? 'text-gray-400' : 'text-white'}`}>
                                {notification.title}
                              </p>
                              {!notification.read && (
                                <span className="w-2 h-2 rounded-full bg-[#2dd4bf] animate-pulse" />
                              )}
                            </div>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{notification.message}</p>
                            <p className="text-xs text-gray-600 mt-2 flex items-center gap-1">
                              <Zap size={10} />
                              {new Date(notification.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-[#2a3441] bg-[#0d1117]/50">
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                  <Sparkles size={12} className="text-[#2dd4bf]" />
                  <span>Powered by CrossFlow AI</span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes scale-in {
          from { opacity: 0; transform: scale(0.95) translateY(10px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slide-in-right {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-scale-in { animation: scale-in 0.3s ease-out; }
        .animate-slide-in-up { animation: slide-in-up 0.4s ease-out both; }
        .animate-slide-in-right { animation: slide-in-right 0.3s ease-out; }
      `}</style>
    </>
  );
};

export default NotificationCenter;
