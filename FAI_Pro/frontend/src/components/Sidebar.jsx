import { Plus, Moon, Sun, Database, History, MapPin, Calendar, Layout } from 'lucide-react'

export default function Sidebar({ 
  counties, 
  years, 
  theme, 
  isOpen,
  onToggleTheme, 
  onPrompt,
  onNewChat
}) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <div className="avatar bot" style={{ width: 24, height: 24, background: 'var(--accent-primary)', color: 'white', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center' }}>
            <Layout size={14} />
          </div>
          <span className="logo-text" style={{ marginLeft: '8px', fontWeight: 600 }}>IrishHome.AI</span>
        </div>
        <button className="theme-toggle" onClick={onToggleTheme} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={18} />
        New Intelligence Session
      </button>

      <div className="sidebar-content">
        <div className="sidebar-group">
          <div className="sidebar-label" style={{ display: 'flex', alignItems: 'center' }}>
             <History size={12} style={{ marginRight: 6 }} />
             Quick Analysis
          </div>
          <button className="nav-item" onClick={() => onPrompt("National rent trends 2024")} style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: '8px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', borderRadius: '8px', color: 'var(--text-secondary)' }}>
            <Layout size={14} />
            National Overview
          </button>
          <button className="nav-item" onClick={() => onPrompt("Affordability score Dublin vs Cork")} style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: '8px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', borderRadius: '8px', color: 'var(--text-secondary)' }}>
            <Layout size={14} />
            Affordability Compare
          </button>
        </div>

        <div className="sidebar-group" style={{ marginTop: 'auto' }}>
          <div className="sidebar-label" style={{ display: 'flex', alignItems: 'center' }}>
            <Database size={12} style={{ marginRight: 6 }} />
            System Data
          </div>
          <div className="ds-chip" style={{ fontSize: '0.7rem', padding: '4px 12px', color: 'var(--text-muted)' }}>RTB Rent Index • Active</div>
          <div className="ds-chip" style={{ fontSize: '0.7rem', padding: '4px 12px', color: 'var(--text-muted)' }}>PPR Property Sale • Active</div>
          <div className="ds-chip" style={{ fontSize: '0.7rem', padding: '4px 12px', color: 'var(--text-muted)' }}>CSO Master Data • Active</div>
        </div>
      </div>

      <div className="sidebar-footer" style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)' }}>
        <div className="nav-item" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
          <Calendar size={14} style={{ marginRight: 8 }} />
          Dataset: Q4 2024
        </div>
      </div>
    </aside>
  )
}
