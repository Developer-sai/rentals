import { useRef, useCallback, useEffect } from 'react'
import { SendHorizontal, Paperclip } from 'lucide-react'

export default function ChatInput({ onSend, disabled }) {
  const textareaRef = useRef(null)

  const autoResize = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  const submit = useCallback(() => {
    const el = textareaRef.current
    if (!el || disabled) return
    const val = el.value.trim()
    if (!val) return
    onSend(val)
    el.value = ''
    el.style.height = '60px' // Reset to default
  }, [onSend, disabled])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (textareaRef.current?.value.trim()) {
        e.preventDefault()
        submit()
      }
    }
  }

  return (
    <div className="input-wrap">
       <button className="btn-icon" style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paperclip size={20} />
      </button>
      
      <textarea
        ref={textareaRef}
        className="chat-textarea"
        placeholder="Ask IrishHome.AI about rents, prices, or affordability..."
        rows={1}
        disabled={disabled}
        onInput={autoResize}
        onKeyDown={onKeyDown}
        style={{ minHeight: '24px', paddingTop: '8px', paddingBottom: '8px' }}
      />
      
      <button
        className="send-btn"
        onClick={submit}
        disabled={disabled}
        style={{ opacity: disabled ? 0.5 : 1 }}
      >
        <SendHorizontal size={18} />
      </button>
    </div>
  )
}
