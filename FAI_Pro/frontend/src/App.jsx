import { useState, useEffect, useRef, useCallback } from 'react'
import { Plus, PanelLeft, Settings, Sparkles, AlertCircle } from 'lucide-react'
import Sidebar from './components/Sidebar'
import MessageBubble, { TypingIndicator } from './components/MessageBubble'
import ChatInput from './components/ChatInput'
import { fetchCounties, fetchYears, sendChat } from './api'

export default function App() {
  const [messages, setMessages]   = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [counties, setCounties]   = useState([])
  const [years, setYears]         = useState([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  
  // Theme state: dark or light
  const [theme, setTheme] = useState('dark')

  const bottomRef = useRef(null)

  useEffect(() => {
    fetchCounties().then(r => setCounties(r.data.counties || [])).catch(() => {})
    fetchYears().then(r => setYears(r.data.years || [])).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen)

  const [status, setStatus] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  const handleSend = useCallback(async (query) => {
    if (!query || isLoading) return

    const userMsg = { id: Date.now(), role: 'user', text: query }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setStatus("Initializing intelligence pipeline...")

    try {
      const response = await fetch('http://127.0.0.1:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId })
      })

      if (!response.ok) throw new Error('Network response was not ok')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() 

        for (const line of lines) {
          const matched = line.match(/^data: (.*)$/m)
          if (matched) {
            try {
              const payload = JSON.parse(matched[1])
              if (payload.type === 'status') {
                setStatus(payload.message)
              } else if (payload.type === 'data') {
                if (payload.session_id) setSessionId(payload.session_id)
                setMessages(prev => [
                  ...prev,
                  { id: Date.now() + 1, role: 'bot', text: payload.answer, data: payload },
                ])
              } else if (payload.type === 'error') {
                throw new Error(payload.message)
              }
            } catch (jsonErr) {
              console.error("SSE JSON Parse error:", jsonErr, line)
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: 'error', text: `Error: ${err.message}` },
      ])
    } finally {
      setIsLoading(false)
      setStatus(null)
    }
  }, [isLoading, sessionId])

  const startNewChat = () => setMessages([])

  return (
    <div className={`app-root ${theme}`}>
      <Sidebar
        counties={counties}
        years={years}
        theme={theme}
        isOpen={isSidebarOpen}
        onToggleTheme={toggleTheme}
        onPrompt={handleSend}
        onNewChat={startNewChat}
      />

      <main className="main-area" role="main">
        {/* Top bar for mobile/desktop toggle */}
        <header className="mobile-header" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-app)' }}>
           <button onClick={toggleSidebar} className="btn-icon" style={{ background: 'none', border: 'none', color: 'var(--text-main)', cursor: 'pointer' }}>
             <PanelLeft size={20} />
           </button>
           {!isSidebarOpen && <span className="logo-text" style={{ marginLeft: '12px', fontWeight: 600 }}>IrishHome.AI</span>}
        </header>

        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome-screen" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', textAlign: 'center' }}>
              <div className="welcome-icon" style={{ background: 'var(--accent-soft)', color: 'var(--accent-primary)', padding: '16px', borderRadius: '50%', marginBottom: '24px' }}>
                <Sparkles size={40} />
              </div>
              <h1 style={{ fontSize: '2rem', marginBottom: '12px' }}>How can I help you with the Irish housing market today?</h1>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', marginBottom: '32px' }}>
                Analyze rents, property prices, and affordability across all 26 counties using official RTB, PPR, and CSO datasets.
              </p>
              
              <div className="suggestion-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', width: '100%', maxWidth: '800px' }}>
                {[
                  "Average rent in Dublin 2024?",
                  "Is Galway affordable for a single person?",
                  "Price trends in Cork since 2015",
                  "Explain Rent Pressure Zones"
                ].map(prompt => (
                  <button 
                    key={prompt} 
                    onClick={() => handleSend(prompt)}
                    className="suggestion-card" 
                    style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', textAlign: 'left', cursor: 'pointer', transition: 'all 0.2s', color: 'var(--text-main)' }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}
          {isLoading && (
            <div className="message-wrapper bot">
              <div className="message-inner">
                <div className="avatar bot">
                   <Sparkles size={16} />
                </div>
                <div className="bubble">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TypingIndicator />
                    {status && <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', animation: 'pulse 2s infinite' }}>{status}</span>}
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} style={{ height: 100 }} />
        </div>

        <div className="input-area">
          <div className="input-container">
            <ChatInput onSend={handleSend} disabled={isLoading} />
            <p className="input-hint">
              <AlertCircle size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
              AI can make mistakes. Consider verifying important financial information.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
