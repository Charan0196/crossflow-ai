import React from 'react'
import ReactDOM from 'react-dom/client'

function MinimalApp() {
  return (
    <div style={{ 
      background: '#0d1117', 
      color: '#10b981', 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      fontFamily: 'monospace'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '48px', marginBottom: '20px' }}>✅ React Works!</h1>
        <p style={{ fontSize: '24px' }}>If you see this, React is rendering correctly.</p>
        <p style={{ color: '#2dd4bf', marginTop: '20px' }}>
          The issue is in one of the imported components.
        </p>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MinimalApp />
  </React.StrictMode>
)
