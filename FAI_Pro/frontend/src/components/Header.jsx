// Header.jsx
import { useEffect, useState } from 'react'
import { checkHealth } from '../api'

export default function Header() {
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <header className="header">
      <a href="/" className="logo" aria-label="IrishHome.AI home">
        <div className="logo-icon" aria-hidden="true">🏡</div>
        <span className="logo-text">IrishHome.AI</span>
      </a>
      <div className="header-right">
        <div
          className={`status-dot${status === 'offline' ? ' offline' : ''}`}
          aria-hidden="true"
        />
        <span>
          {status === 'connecting' ? 'Connecting…'
           : status === 'online'   ? 'AI Ready'
           : 'Backend Offline'}
        </span>
      </div>
    </header>
  )
}
