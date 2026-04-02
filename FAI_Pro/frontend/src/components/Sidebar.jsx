export default function Sidebar({ theme, onToggleTheme, onPrompt }) {
  const PROMPTS = [
    "What is the average rent in Dublin?",
    "Compare rent in Cork vs Galway",
    "Show me rent trends in Limerick",
    "Is housing affordable in Waterford?",
    "What is the average house price in Dublin?",
    "Which county has the cheapest rent?",
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <a href="/" className="logo">
          <span className="logo-icon">⌂</span>
          <span>Property AI</span>
        </a>
        <button onClick={onToggleTheme} className="theme-toggle" title="Toggle Theme">
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>

      <div className="sidebar-section" style={{ flex: 1, overflowY: 'auto' }}>
        <p className="sidebar-title">Suggested Prompts</p>
        {PROMPTS.map(p => (
          <button
            key={p}
            className="prompt-chip"
            onClick={() => onPrompt(p)}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="sidebar-section" style={{ marginTop: 'auto', marginBottom: 0 }}>
        <p className="sidebar-title">Datasets Loaded</p>
        <div className="ds-chip"><span>RTB Rent Data</span><span>Active</span></div>
        <div className="ds-chip"><span>CSO Statistics</span><span>Active</span></div>
        <div className="ds-chip"><span>PPR House Prices</span><span>Active</span></div>
      </div>
    </aside>
  )
}
