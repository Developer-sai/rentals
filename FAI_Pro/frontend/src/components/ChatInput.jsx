import { useRef, useCallback } from 'react'

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
    el.style.height = 'auto'
  }, [onSend, disabled])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="input-wrap">
      <textarea
        ref={textareaRef}
        className="chat-textarea"
        placeholder="Ask property queries..."
        rows={1}
        disabled={disabled}
        onInput={autoResize}
        onKeyDown={onKeyDown}
      />
      <button
        className="send-btn"
        onClick={submit}
        disabled={disabled || !textareaRef.current?.value.trim()}
      >
        ↑
      </button>
    </div>
  )
}
