import React, { useState, useEffect } from 'react'
import { Brain, Sparkles, Zap, Check, ChevronDown } from 'lucide-react'

const AI_PROVIDERS = [
  { 
    id: 'groq', 
    name: 'Groq', 
    icon: '⚡', 
    color: '#F55036',
    description: 'FREE & Super Fast!',
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    badge: 'FREE'
  },
  { 
    id: 'huggingface', 
    name: 'Hugging Face', 
    icon: '🤗', 
    color: '#FFD21E',
    description: 'FREE tier available',
    models: ['meta-llama/Llama-3.2-3B-Instruct', 'mistralai/Mistral-7B-Instruct-v0.3'],
    badge: 'FREE'
  },
  { 
    id: 'gemini', 
    name: 'Google Gemini', 
    icon: '✨', 
    color: '#4285F4',
    description: 'Advanced analysis',
    models: ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro'],
    badge: 'FREE TIER'
  },
  { 
    id: 'openai', 
    name: 'OpenAI', 
    icon: '🤖', 
    color: '#10A37F',
    description: 'Reliable and accurate',
    models: ['gpt-4', 'gpt-3.5-turbo']
  },
  { 
    id: 'claude', 
    name: 'Claude', 
    icon: '🎭', 
    color: '#D97706',
    description: 'High quality responses',
    models: ['claude-3-opus', 'claude-3-sonnet']
  }
]

const AIProviderSelector = ({ onProviderChange, selectedProvider = 'groq', onModelChange, selectedModel }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [availableProviders, setAvailableProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentProvider, setCurrentProvider] = useState(selectedProvider)
  const [currentModel, setCurrentModel] = useState(selectedModel)

  useEffect(() => {
    fetchAvailableProviders()
    // Initialize model if not set
    if (!currentModel && selectedProvider) {
      const provider = AI_PROVIDERS.find(p => p.id === selectedProvider)
      if (provider && provider.models.length > 0) {
        const defaultModel = provider.models[0]
        setCurrentModel(defaultModel)
        if (onModelChange) {
          onModelChange(defaultModel)
        }
      }
    }
  }, [selectedProvider])

  const fetchAvailableProviders = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/multi-ai/providers')
      const data = await response.json()
      
      if (data.success) {
        const enabledIds = data.providers.map(p => p.name)
        setAvailableProviders(enabledIds)
      }
    } catch (error) {
      console.error('Failed to fetch AI providers:', error)
      // Default to all providers if fetch fails
      setAvailableProviders(AI_PROVIDERS.map(p => p.id))
    } finally {
      setLoading(false)
    }
  }

  const handleProviderSelect = (providerId) => {
    setCurrentProvider(providerId)
    setIsOpen(false)
    if (onProviderChange) {
      onProviderChange(providerId)
    }
    // Reset model when provider changes
    const provider = AI_PROVIDERS.find(p => p.id === providerId)
    if (provider && provider.models.length > 0) {
      const defaultModel = provider.models[0]
      setCurrentModel(defaultModel)
      if (onModelChange) {
        onModelChange(defaultModel)
      }
    }
  }

  const handleModelSelect = (model) => {
    setCurrentModel(model)
    if (onModelChange) {
      onModelChange(model)
    }
  }

  const selectedProviderData = AI_PROVIDERS.find(p => p.id === currentProvider) || AI_PROVIDERS[0]
  const enabledProviders = AI_PROVIDERS.filter(p => availableProviders.includes(p.id))

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg">
        <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-gray-400">Loading AI providers...</span>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/30 rounded-lg hover:border-purple-500/50 transition-all"
      >
        <span className="text-2xl">{selectedProviderData.icon}</span>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <Brain size={14} className="text-purple-400" />
            <span className="text-sm font-semibold text-white">{selectedProviderData.name}</span>
            {currentModel && (
              <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-300 rounded">
                {currentModel ? currentModel.split('-').pop().split('/').pop() : 'default'}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400">{selectedProviderData.description}</p>
        </div>
        <ChevronDown 
          size={16} 
          className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute top-full left-0 mt-2 w-80 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 shadow-2xl">
            <div className="px-4 py-2 border-b border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles size={14} className="text-cyan-400" />
                <span className="text-xs font-semibold text-cyan-400">AI PROVIDERS</span>
              </div>
              <p className="text-xs text-gray-500">
                {enabledProviders.length} of {AI_PROVIDERS.length} providers available
              </p>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {AI_PROVIDERS.map((provider) => {
                const isEnabled = availableProviders.includes(provider.id)
                const isSelected = currentProvider === provider.id

                return (
                  <button
                    key={provider.id}
                    onClick={() => isEnabled && handleProviderSelect(provider.id)}
                    disabled={!isEnabled}
                    className={`w-full px-4 py-3 text-left transition-colors flex items-center gap-3 ${
                      isEnabled 
                        ? 'hover:bg-gray-700 cursor-pointer' 
                        : 'opacity-50 cursor-not-allowed'
                    } ${isSelected ? 'bg-gray-700/50' : ''}`}
                  >
                    <span className="text-2xl">{provider.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-white">{provider.name}</p>
                        {provider.badge && isEnabled && (
                          <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded font-bold">
                            {provider.badge}
                          </span>
                        )}
                        {!isEnabled && (
                          <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                            Disabled
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400">{provider.description}</p>
                      <div className="flex items-center gap-1 mt-1">
                        <Zap size={10} className="text-gray-500" />
                        <span className="text-xs text-gray-500">
                          {provider.models.length} models
                        </span>
                      </div>
                      {isSelected && isEnabled && provider.models.length > 1 && (
                        <div className="mt-2 space-y-1">
                          <p className="text-xs text-gray-400 font-medium">Models:</p>
                          <div className="flex flex-wrap gap-1">
                            {provider.models.map((model) => (
                              <button
                                key={model}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleModelSelect(model)
                                }}
                                className={`text-xs px-2 py-1 rounded transition-colors ${
                                  currentModel === model
                                    ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                              >
                                {model.split('-').pop().split('/').pop()}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    {isSelected && isEnabled && (
                      <Check size={16} className="text-green-500" />
                    )}
                  </button>
                )
              })}
            </div>

            <div className="px-4 py-2 border-t border-gray-700 mt-2">
              <p className="text-xs text-gray-500">
                💡 Configure API keys in backend .env file to enable providers
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default AIProviderSelector
