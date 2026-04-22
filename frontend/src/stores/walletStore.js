import { create } from 'zustand'

const DEMO_WALLET = "0x6739659248061A54E0f4de8f2cd60278B69468b3"

export const useWalletStore = create((set, get) => ({
  address: DEMO_WALLET,
  ethBalance: "0.0000",
  tokenBalances: [],
  isConnected: true,
  isTrading: false,
  lastUpdate: 0,
  useConnectedWallet: false, // New flag to use connected wallet instead of demo

  // Set to use connected wallet instead of demo
  setUseConnectedWallet: (useConnected, connectedAddress = null) => {
    set({ 
      useConnectedWallet: useConnected,
      address: useConnected && connectedAddress ? connectedAddress : DEMO_WALLET
    })
  },

  initialize: async (connectedAddress = null) => {
    const { useConnectedWallet } = get()
    const targetAddress = (useConnectedWallet && connectedAddress) ? connectedAddress : DEMO_WALLET
    
    try {
      const response = await fetch(`http://localhost:8000/api/autonomous/wallet/balance?address=${targetAddress}`)
      const data = await response.json()
      
      set({
        address: targetAddress,
        ethBalance: data.eth_balance,
        tokenBalances: data.token_balances,
        isConnected: true,
        lastUpdate: data.last_update
      })
    } catch (error) {
      console.error('Failed to initialize wallet:', error)
      // Fallback to demo data
      set({
        address: targetAddress,
        ethBalance: "0.0000",
        tokenBalances: [],
        isConnected: true,
        lastUpdate: Date.now()
      })
    }
  },

  updateBalance: async (connectedAddress = null) => {
    const { initialize } = get()
    await initialize(connectedAddress)
  },

  setTrading: (status) => {
    set({ isTrading: status })
  }
}))
