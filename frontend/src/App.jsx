import { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { Wallet, XCircle, Settings, X, LogOut } from 'lucide-react';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TradingPage from './pages/TradingPage';
import PortfolioPage from './pages/PortfolioPage';
import AITerminalPage from './pages/AITerminalPage';
import AutonomousPage from './pages/AutonomousPage';
import AutoTradingDashboard from './components/trading/AutoTradingDashboard';
import RealFundsDashboard from './components/trading/RealFundsDashboard';
import RiskPage from './pages/RiskPage';
import MEVShieldPage from './pages/MEVShieldPage';
import SolversPage from './pages/SolversPage';
import GasPage from './pages/GasPage';
import MarketplacePage from './pages/MarketplacePage';
import RWAPage from './pages/RWAPage';
import CompliancePage from './pages/CompliancePage';
import ZKProofsPage from './pages/ZKProofsPage';

// Logo SVG Component
const Logo = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="16" r="14" stroke="#2dd4bf" strokeWidth="2" fill="none"/>
    <circle cx="16" cy="16" r="6" fill="#2dd4bf"/>
    <circle cx="16" cy="6" r="3" fill="#2dd4bf"/>
    <circle cx="16" cy="26" r="3" fill="#2dd4bf"/>
    <circle cx="6" cy="16" r="3" fill="#2dd4bf"/>
    <circle cx="26" cy="16" r="3" fill="#2dd4bf"/>
  </svg>
);

// Wallet Connector
const WalletConnector = () => {
  const { address, isConnected } = useAccount();
  const { connect, connectors, isPending, error } = useConnect();
  const { disconnect } = useDisconnect();
  const [showModal, setShowModal] = useState(false);
  const [connectError, setConnectError] = useState(null);
  const [isSwitching, setIsSwitching] = useState(false);

  const getWalletIcon = (name) => {
    if (name.toLowerCase().includes('metamask')) return '🦊';
    if (name.toLowerCase().includes('coinbase')) return '🔵';
    if (name.toLowerCase().includes('walletconnect')) return '🔗';
    if (name.toLowerCase().includes('injected')) return '💉';
    return '👛';
  };

  const forceAccountSelection = async () => {
    if (!window.ethereum) return false;
    
    try {
      console.log('🔄 Attempting to force account selection...');
      
      // Step 1: Clear only wagmi-related storage (not all localStorage)
      console.log('Clearing wagmi storage...');
      localStorage.removeItem('wagmi.recentConnectorId');
      localStorage.removeItem('wagmi.connected');
      localStorage.removeItem('wagmi.cache');
      localStorage.removeItem('wagmi.store');
      
      // Step 2: Wait for cleanup
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Step 3: Try to request accounts (this should show MetaMask popup)
      try {
        console.log('Requesting accounts...');
        const accounts = await window.ethereum.request({
          method: 'eth_requestAccounts',
          params: []
        });
        
        console.log('✅ Accounts selected:', accounts);
        return accounts;
      } catch (requestError) {
        console.log('Direct request failed, trying permission flow...');
        
        // Alternative: Use permission flow
        await window.ethereum.request({
          method: 'wallet_requestPermissions',
          params: [{ eth_accounts: {} }]
        });
        
        const accounts = await window.ethereum.request({
          method: 'eth_requestAccounts'
        });
        
        console.log('✅ Accounts via permission flow:', accounts);
        return accounts;
      }
    } catch (error) {
      console.error('❌ Force account selection failed:', error);
      return false;
    }
  };

  const handleConnect = async (connector) => {
    try {
      setConnectError(null);
      
      // For MetaMask, use targeted account selection
      if (connector.name.toLowerCase().includes('metamask')) {
        console.log('🔄 MetaMask connection starting...');
        
        // Step 1: Disconnect current connection if exists
        if (isConnected) {
          console.log('Disconnecting current connection...');
          disconnect();
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Step 2: Clear only wagmi-specific cached data (not all localStorage)
        console.log('Clearing wagmi cache...');
        localStorage.removeItem('wagmi.recentConnectorId');
        localStorage.removeItem('wagmi.connected');
        localStorage.removeItem('wagmi.cache');
        localStorage.removeItem('wagmi.store');
        
        // Step 3: Try to request fresh account selection
        if (window.ethereum && window.ethereum.request) {
          try {
            console.log('🔐 Requesting MetaMask account access...');
            
            // Try to revoke permissions first (optional)
            try {
              await window.ethereum.request({
                method: 'wallet_revokePermissions',
                params: [{ eth_accounts: {} }]
              });
              console.log('✅ Revoked existing permissions');
            } catch (revokeError) {
              console.log('⚠️ Could not revoke permissions (this is normal):', revokeError.message);
            }
            
            // Request fresh permissions to trigger account selection
            console.log('Requesting fresh permissions...');
            await window.ethereum.request({
              method: 'wallet_requestPermissions',
              params: [{ eth_accounts: {} }]
            });
            
            console.log('✅ Permissions granted');
            
          } catch (permError) {
            console.log('❌ Permission request failed:', permError.message);
            // Don't throw error here, let wagmi handle the connection
          }
        }
      }
      
      // Step 4: Connect with wagmi (this should trigger MetaMask popup)
      console.log('Connecting with wagmi...');
      await connect({ connector });
      setShowModal(false);
      console.log('✅ Connection successful');
      
    } catch (err) {
      console.error('❌ Connection error:', err);
      setConnectError(err.message || 'Failed to connect. Please make sure MetaMask is installed and unlocked.');
    }
  };

  const handleDisconnect = () => {
    console.log('Disconnecting all wallets...');
    
    // Disconnect wagmi
    disconnect();
    
    // Clear all wagmi and wallet-related localStorage data
    if (typeof window !== 'undefined') {
      // Clear wagmi storage
      localStorage.removeItem('wagmi.connected');
      localStorage.removeItem('wagmi.wallet');
      localStorage.removeItem('wagmi.cache');
      localStorage.removeItem('wagmi.store');
      localStorage.removeItem('wagmi.recentConnectorId');
      localStorage.removeItem('wagmi.injected.shimDisconnect');
      
      // Clear WalletConnect storage
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('walletconnect') || 
            key.startsWith('wc@2') || 
            key.startsWith('@walletconnect')) {
          localStorage.removeItem(key);
        }
      });
      
      // Clear MetaMask storage
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('metamask') || 
            key.startsWith('MetaMask') ||
            key.startsWith('-walletlink')) {
          localStorage.removeItem(key);
        }
      });
      
      // Clear Coinbase Wallet storage
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('coinbase') || 
            key.startsWith('cbw') ||
            key.startsWith('walletlink')) {
          localStorage.removeItem(key);
        }
      });
      
      // Clear any other wallet-related storage
      Object.keys(localStorage).forEach(key => {
        if (key.includes('wallet') || 
            key.includes('connect') ||
            key.includes('injected')) {
          localStorage.removeItem(key);
        }
      });
      
      // Clear sessionStorage as well
      Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('wagmi') || 
            key.startsWith('walletconnect') ||
            key.startsWith('metamask') ||
            key.includes('wallet')) {
          sessionStorage.removeItem(key);
        }
      });
      
      console.log('All wallet storage cleared');
    }
    
    // Force page reload to ensure clean state
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  // Make disconnect function available globally for console access
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.disconnectAllWallets = handleDisconnect;
      
      // Add MetaMask testing functions
      window.testMetaMaskSwitch = async () => {
        console.log('🔧 Testing MetaMask Account Switch...');
        
        try {
          // Step 1: Check current accounts
          const currentAccounts = await window.ethereum.request({
            method: 'eth_accounts'
          });
          console.log('Current accounts:', currentAccounts);
          
          // Step 2: Clear permissions
          try {
            await window.ethereum.request({
              method: 'wallet_revokePermissions',
              params: [{ eth_accounts: {} }]
            });
            console.log('✅ Permissions revoked');
          } catch (error) {
            console.log('⚠️ Could not revoke permissions:', error.message);
          }
          
          // Step 3: Request fresh permissions
          await window.ethereum.request({
            method: 'wallet_requestPermissions',
            params: [{ eth_accounts: {} }]
          });
          console.log('✅ Fresh permissions requested');
          
          // Step 4: Get new accounts
          const newAccounts = await window.ethereum.request({
            method: 'eth_requestAccounts'
          });
          console.log('New accounts:', newAccounts);
          
          if (currentAccounts[0] !== newAccounts[0]) {
            console.log('🎉 Account switch successful!');
            console.log(`From: ${currentAccounts[0]}`);
            console.log(`To: ${newAccounts[0]}`);
          } else {
            console.log('ℹ️ Same account selected');
          }
          
        } catch (error) {
          console.error('❌ Test failed:', error);
        }
      };
      
      // Check if we just reloaded for account switch
      if (localStorage.getItem('force_account_switch') === 'true') {
        localStorage.removeItem('force_account_switch');
        console.log('Page reloaded for account switch, will prompt for account selection...');
        
        // Wait a moment then show connection modal
        setTimeout(() => {
          setShowModal(true);
        }, 2000);
      }
    }
  }, []);

  // Show different UI based on connection status
  if (isConnected && address) {
    // Connected state - show address and disconnect option
    return (
      <>
        <button 
          onClick={() => {
            setConnectError(null);
            setShowModal(true);
          }} 
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold text-sm transition-all"
        >
          <div className="w-2 h-2 rounded-full bg-green-300 animate-pulse" />
          <span className="font-mono">{address.slice(0, 6)}...{address.slice(-4)}</span>
        </button>
        
        {showModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => {
              setShowModal(false);
              setConnectError(null);
            }} />
            <div className="relative bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">Wallet Connected</h3>
                <button onClick={() => {
                  setShowModal(false);
                  setConnectError(null);
                }} className="p-1 rounded-lg hover:bg-gray-800">
                  <XCircle size={22} className="text-gray-400" />
                </button>
              </div>
              
              {connectError && (
                <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                  {connectError}
                </div>
              )}
              
              <div className="mb-6 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
                  <p className="text-green-400 font-medium">Connected</p>
                </div>
                <p className="text-white font-mono text-lg mb-2">{address}</p>
                <p className="text-gray-400 text-sm">Ready for transactions</p>
              </div>
              
              <div className="space-y-3">
                <button 
                  onClick={async () => {
                    try {
                      setIsSwitching(true);
                      setConnectError(null);
                      setShowModal(false);
                      
                      // Disconnect current connection first
                      disconnect();
                      
                      // Wait for disconnect to complete
                      await new Promise(resolve => setTimeout(resolve, 1500));
                      
                      // Clear cached connection data more aggressively
                      localStorage.removeItem('wagmi.recentConnectorId');
                      localStorage.removeItem('wagmi.connected');
                      localStorage.removeItem('wagmi.cache');
                      localStorage.removeItem('wagmi.store');
                      
                      // Try the force account selection method first
                      const forceResult = await forceAccountSelection();
                      
                      if (forceResult) {
                        // Force method worked, now reconnect
                        const metamaskConnector = connectors.find(c => 
                          c.name.toLowerCase().includes('metamask')
                        );
                        
                        if (metamaskConnector) {
                          await connect({ connector: metamaskConnector });
                        }
                      } else {
                        // Fallback to permission-based method
                        if (window.ethereum && window.ethereum.request) {
                          try {
                            // Method 1: Try to revoke existing permissions first
                            try {
                              await window.ethereum.request({
                                method: 'wallet_revokePermissions',
                                params: [{ eth_accounts: {} }]
                              });
                              console.log('Revoked existing permissions for account switch');
                            } catch (revokeError) {
                              console.log('Could not revoke permissions:', revokeError.message);
                            }
                            
                            // Method 2: Request fresh permissions to force account selection
                            await window.ethereum.request({
                              method: 'wallet_requestPermissions',
                              params: [{ eth_accounts: {} }]
                            });
                            
                            // Method 3: Request accounts after permission grant
                            const accounts = await window.ethereum.request({
                              method: 'eth_requestAccounts'
                            });
                            
                            console.log('Switched to accounts:', accounts);
                            
                            // Find MetaMask connector and reconnect
                            const metamaskConnector = connectors.find(c => 
                              c.name.toLowerCase().includes('metamask')
                            );
                            
                            if (metamaskConnector) {
                              await connect({ connector: metamaskConnector });
                            }
                            
                          } catch (error) {
                            console.error('Account switch error:', error);
                            setConnectError('Failed to switch account. Please try connecting again.');
                          }
                        }
                      }
                    } catch (error) {
                      console.error('Account switch error:', error);
                      setConnectError('Failed to switch account. Please try connecting again.');
                    } finally {
                      setIsSwitching(false);
                    }
                  }}
                  disabled={isSwitching}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all"
                >
                  {isSwitching ? 'Switching Account...' : 'Switch Account'}
                </button>
                
                <button 
                  onClick={() => {
                    // Show manual instructions
                    const instructions = `Manual Account Switch Instructions:

1. Open MetaMask extension
2. Click on your account icon (top right)
3. Select "Connected Sites" or "Settings" → "Connected Sites"
4. Find "localhost:5173" and click "Disconnect"
5. Close this dialog and click "Connect Wallet" again
6. MetaMask should now show account selection

Alternative method:
1. Open MetaMask
2. Click the account dropdown
3. Select a different account
4. Refresh this page
5. Connect again`;
                    
                    alert(instructions);
                  }}
                  className="w-full py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm transition-all"
                >
                  Manual Switch Instructions
                </button>
                
                <button 
                  onClick={async () => {
                    try {
                      setConnectError(null);
                      setShowModal(false);
                      
                      console.log('Starting targeted reset for account selection...');
                      
                      // Disconnect wagmi
                      disconnect();
                      
                      // Clear only wallet-related storage (not all localStorage)
                      localStorage.removeItem('wagmi.recentConnectorId');
                      localStorage.removeItem('wagmi.connected');
                      localStorage.removeItem('wagmi.cache');
                      localStorage.removeItem('wagmi.store');
                      
                      // Clear MetaMask-specific items only
                      Object.keys(localStorage).forEach(key => {
                        if (key.startsWith('metamask') || 
                            key.startsWith('walletconnect') ||
                            key.includes('wallet') && key.includes('connect')) {
                          localStorage.removeItem(key);
                        }
                      });
                      
                      // Wait a moment
                      await new Promise(resolve => setTimeout(resolve, 1000));
                      
                      // Set flag and reload page to force fresh connection
                      localStorage.setItem('force_account_switch', 'true');
                      window.location.reload();
                      
                    } catch (error) {
                      console.error('Force reset error:', error);
                      setConnectError('Reset failed. Please try manually disconnecting in MetaMask.');
                    }
                  }}
                  className="w-full py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm transition-all"
                >
                  Force Account Selection (Reset & Reload)
                </button>
                
                <button 
                  onClick={() => {
                    handleDisconnect();
                    setShowModal(false);
                  }}
                  className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-all"
                >
                  Disconnect Wallet
                </button>
                
                <button 
                  onClick={() => {
                    // Force disconnect and clear everything
                    handleDisconnect();
                  }}
                  className="w-full py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-all"
                >
                  Clear All Wallet Data & Reload
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Not connected state - show connect button
  return (
    <>
      <button 
        onClick={() => {
          setConnectError(null);
          setShowModal(true);
        }} 
        className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#2dd4bf] text-black font-semibold text-sm hover:bg-[#5eead4] transition-all"
        data-wallet-connect
      >
        <Wallet size={16} />
        Connect Wallet
      </button>
      
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => {
            setShowModal(false);
            setConnectError(null);
          }} />
          <div className="relative bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white">Connect Wallet</h3>
              <button onClick={() => {
                setShowModal(false);
                setConnectError(null);
              }} className="p-1 rounded-lg hover:bg-gray-800">
                <XCircle size={22} className="text-gray-400" />
              </button>
            </div>
            
            {(connectError || error) && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {connectError || error?.message || 'Connection failed. Please try again.'}
              </div>
            )}
            
            <div className="space-y-2">
              {connectors.filter(c => c.ready).map((connector) => (
                <button 
                  key={connector.id} 
                  onClick={() => handleConnect(connector)} 
                  disabled={isPending}
                  className="w-full flex items-center gap-4 p-4 rounded-xl bg-[#0d1117] border border-[#2a3441] hover:border-[#2dd4bf] transition-all disabled:opacity-50"
                >
                  <span className="text-2xl">{getWalletIcon(connector.name)}</span>
                  <div className="flex-1 text-left">
                    <span className="font-medium text-white">{connector.name}</span>
                    {connector.name.toLowerCase().includes('metamask') && (
                      <p className="text-xs text-gray-500">
                        {localStorage.getItem('force_account_switch') ? 
                          'Select different account in MetaMask' : 
                          'Will prompt for account selection'
                        }
                      </p>
                    )}
                    {connector.name.toLowerCase().includes('walletconnect') && (
                      <p className="text-xs text-gray-500">Scan QR code</p>
                    )}
                    {connector.name.toLowerCase().includes('coinbase') && (
                      <p className="text-xs text-gray-500">Coinbase Wallet</p>
                    )}
                  </div>
                  {isPending && <span className="text-xs text-gray-400">Connecting...</span>}
                </button>
              ))}
              
              {/* Add basic connect button for MetaMask */}
              {connectors.find(c => c.name.toLowerCase().includes('metamask')) && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <p className="text-xs text-gray-400 mb-2 text-center">Alternative Connection Method:</p>
                  <button 
                    onClick={async () => {
                      try {
                        setConnectError(null);
                        console.log('🔄 Basic MetaMask connection (no account switching)...');
                        
                        const metamaskConnector = connectors.find(c => 
                          c.name.toLowerCase().includes('metamask')
                        );
                        
                        if (metamaskConnector) {
                          await connect({ connector: metamaskConnector });
                          setShowModal(false);
                          console.log('✅ Basic connection successful');
                        }
                      } catch (error) {
                        console.error('❌ Basic connection failed:', error);
                        setConnectError(error.message || 'Connection failed');
                      }
                    }}
                    disabled={isPending}
                    className="w-full flex items-center gap-4 p-3 rounded-xl bg-green-600 hover:bg-green-700 border border-green-500 transition-all disabled:opacity-50"
                  >
                    <span className="text-xl">🦊</span>
                    <div className="flex-1 text-left">
                      <span className="font-medium text-white">MetaMask (Basic Connect)</span>
                      <p className="text-xs text-green-200">Simple connection - no account switching</p>
                    </div>
                    {isPending && <span className="text-xs text-gray-200">Connecting...</span>}
                  </button>
                </div>
              )}
            </div>
            
            <p className="mt-4 text-xs text-gray-500 text-center">
              By connecting, you agree to the Terms of Service
            </p>
          </div>
        </div>
      )}
    </>
  );
};

// Features Dropdown
const FeaturesDropdown = ({ setActiveSection }) => {
  const [open, setOpen] = useState(false);
  const features = [
    { id: 'autonomous', label: 'Autonomous Trading' },
    { id: 'auto-trading', label: 'Auto Trading (Mock)' },
    { id: 'real-funds', label: 'Real Funds (Display Only)' },
    { id: 'risk', label: 'Risk Analysis' },
    { id: 'mev', label: 'MEV Shield' },
    { id: 'compliance', label: 'Compliance' },
    { id: 'zk-proofs', label: 'ZK-Proofs' }
  ];

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="p-2 rounded-lg bg-[#1a1f2e] border border-[#2a3441] hover:border-[#2dd4bf] transition-all">
        <Settings size={18} className="text-gray-400" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-full right-0 mt-2 w-44 bg-[#1a1f2e] border border-[#2a3441] rounded-xl py-2 z-50 shadow-xl">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[#2a3441]">
              <span className="text-[#2dd4bf] font-medium text-sm">Features</span>
              <button onClick={() => setOpen(false)}><X size={14} className="text-gray-400" /></button>
            </div>
            {features.map(f => (
              <button key={f.id} onClick={() => { setActiveSection(f.id); setOpen(false); }}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-[#2a3441] transition-colors">
                {f.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// Main Dashboard Layout
const CrossFlowDashboard = () => {
  const { logout } = useAuthStore();
  const [activeSection, setActiveSection] = useState('dashboard');

  const mainNav = ['Dashboard', 'Trading', 'Portfolio', 'AI Terminal'];
  const navMap = { 'Dashboard': 'dashboard', 'Trading': 'trading', 'Portfolio': 'portfolio', 'AI Terminal': 'ai-chat' };

  const renderPage = () => {
    switch (activeSection) {
      case 'dashboard': return <DashboardPage onNavigate={setActiveSection} />;
      case 'trading': return <TradingPage />;
      case 'portfolio': return <PortfolioPage />;
      case 'ai-chat': return <AITerminalPage />;
      case 'autonomous': return <AutonomousPage />;
      case 'auto-trading': return <AutoTradingDashboard />;
      case 'real-funds': return <RealFundsDashboard />;
      case 'risk': return <RiskPage />;
      case 'mev': return <MEVShieldPage />;
      case 'solvers': return <SolversPage />;
      case 'gas': return <GasPage />;
      case 'marketplace': return <MarketplacePage />;
      case 'rwa': return <RWAPage />;
      case 'compliance': return <CompliancePage />;
      case 'zk-proofs': return <ZKProofsPage />;
      default: return <DashboardPage onNavigate={setActiveSection} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* Header */}
      <header className="px-8 py-4 border-b border-[#1e2530]">
        <div className="max-w-[1400px] mx-auto flex items-center justify-between">
          {/* Logo & Nav */}
          <div className="flex items-center gap-10">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveSection('dashboard')}>
              <Logo />
              <span className="text-xl font-bold tracking-tight">CROSSFLOW <span className="text-[#2dd4bf]">AI</span></span>
            </div>
            <nav className="hidden md:flex items-center gap-2">
              {mainNav.map(item => (
                <button key={item} onClick={() => setActiveSection(navMap[item])}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === navMap[item] ? 'text-white' : 'text-gray-400 hover:text-white'
                  }`}>
                  {item}
                </button>
              ))}
            </nav>
          </div>
          {/* Right */}
          <div className="flex items-center gap-3">
            <FeaturesDropdown setActiveSection={setActiveSection} />
            <WalletConnector />
            <button 
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all"
              title="Logout"
            >
              <LogOut size={16} />
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        </div>
      </header>
      {/* Main */}
      <main className="px-8 py-6">
        <div className="max-w-[1400px] mx-auto">{renderPage()}</div>
      </main>
    </div>
  );
};

function App() {
  const { isAuthenticated, initializeAuth } = useAuthStore();
  useEffect(() => { initializeAuth(); }, [initializeAuth]);
  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />} />
      <Route path="/*" element={isAuthenticated ? <CrossFlowDashboard /> : <Navigate to="/login" />} />
    </Routes>
  );
}

export default App;
