import { useState, useEffect, useRef, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import MessageBubble, { TypingIndicator } from './components/MessageBubble'
import ChatInput from './components/ChatInput'
import { fetchCounties, fetchYears, sendChat } from './api'

export default function App() {
  const [messages, setMessages]   = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [counties, setCounties]   = useState([])
  const [years, setYears]         = useState([])
  
  // Theme state: dark or light
  const [theme, setTheme] = useState('dark')

  const bottomRef = useRef(null)

  useEffect(() => {
    fetchCounties().then(r => setCounties(r.data.counties || [])).catch(() => {})
    fetchYears().then(r => setYears(r.data.years || [])).catch(() => {})
    
    // Set an initial greeting message mimicking ChatGPT
    setMessages([
      { 
        id: 'welcome', 
        role: 'bot', 
        text: 'Hello. I am your Irish Property Intelligence Assistant.\n\nI can analyze rents, property prices, long-term trends, and structural affordability across all 26 counties using official RTB and CSO datasets. How can I help you today?' 
      }
    ])
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark')

  const handleSend = useCallback(async (query) => {
    if (!query || isLoading) return

    setMessages(prev => [...prev, { id: Date.now(), role: 'user', text: query }])
    setIsLoading(true)

    try {
      const res = await sendChat(query)
      const data = res.data
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: 'bot', text: data.answer, data },
      ])
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to reach backend.'
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: 'error', text: `Error: ${detail}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  return (
    <div className={`app-root ${theme}`}>
      <Sidebar
        counties={counties}
        years={years}
        theme={theme}
        onToggleTheme={toggleTheme}
        onPrompt={handleSend}
      />

      <main className="main-area" role="main">
        <div className="chat-container">
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="message-wrapper bot">
              <div className="message-inner">
                <div className="avatar bot">A</div>
                <div className="bubble">
                  <TypingIndicator />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} style={{ height: 40 }} />
        </div>

        <div className="input-area">
          <ChatInput onSend={handleSend} disabled={isLoading} />
          <p className="input-hint">
            AI can make mistakes. Consider verifying important financial information.
          </p>
        </div>
      </main>
    </div>
  )
}
