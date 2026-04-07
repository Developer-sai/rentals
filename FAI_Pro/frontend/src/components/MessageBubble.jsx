import { useEffect } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, RadialLinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'
import { Bar, Line, Doughnut, PolarArea, Radar } from 'react-chartjs-2'
import ReactMarkdown from 'react-markdown'
import { Sparkles, User, Info, CheckCircle2, ExternalLink, Globe } from 'lucide-react'

ChartJS.register(
  CategoryScale, LinearScale, RadialLinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  animation: { duration: 800, easing: 'easeOutQuart' },
  plugins: {
    legend: { 
      display: false,
      labels: { font: { family: 'Inter', size: 12, weight: '500' }, color: 'var(--text-secondary)' }
    },
    tooltip: {
      backgroundColor: '#111827', 
      titleColor: '#fff', 
      bodyColor: '#d1d5db',
      padding: 12, 
      borderColor: 'rgba(255,255,255,0.1)', 
      borderWidth: 1,
      cornerRadius: 12,
      displayColors: false
    },
  },
  scales: {
    x: { 
      grid: { display: false }, 
      ticks: { color: 'var(--text-muted)', font: { family: 'Inter', size: 11 } } 
    },
    y: { 
      border: { dash: [4, 4] },
      grid: { color: 'rgba(156, 163, 175, 0.1)' }, 
      ticks: { color: 'var(--text-muted)', font: { family: 'Inter', size: 11 } } 
    },
  },
}

function ChartPanel({ chartData }) {
  if (!chartData) return null
  const { type, labels, values, title } = chartData
  
  // Professional Enterprise Palette
  const colors = {
    primary: '#10a37f', // Emerald
    secondary: '#6366f1', // Indigo
    accent: '#f59e0b', // Amber
    muted: '#94a3b8', // Slate
    gradients: [
      'rgba(16, 163, 127, 0.8)',
      'rgba(16, 163, 127, 0.6)',
      'rgba(16, 163, 127, 0.4)',
      'rgba(16, 163, 127, 0.2)',
    ]
  }
  
  const dataset = {
    labels,
    datasets: [{
      label: title, 
      data: values,
      backgroundColor: type === 'doughnut' ? ['#10a37f', '#1e293b'] : 'rgba(16, 163, 127, 0.15)',
      borderColor: colors.primary,
      borderWidth: type === 'line' ? 3 : 1,
      pointBackgroundColor: colors.primary,
      pointBorderColor: '#fff',
      pointHoverRadius: 6,
      fill: type === 'line',
      tension: 0.4, // Smooth Bezier curves
      borderRadius: type === 'bar' ? 6 : 0,
    }],
  }

  const opts = JSON.parse(JSON.stringify(chartOptions))
  if (type === 'doughnut' || type === 'polarArea') {
    opts.scales = {}
    opts.plugins.legend = { display: true, position: 'bottom' }
  }

  return (
    <div className="chart-panel" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '20px', marginTop: '16px' }}>
      <div className="chart-title" style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
         <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-primary)' }} />
         {title}
      </div>
      <div className="chart-wrap" style={{ minHeight: '200px' }}>
        {type === 'line' && <Line data={dataset} options={opts} />}
        {type === 'bar' && <Bar data={dataset} options={opts} />}
        {type === 'doughnut' && <Doughnut data={dataset} options={opts} />}
        {type === 'polarArea' && <PolarArea data={dataset} options={opts} />}
        {type === 'radar' && <Radar data={dataset} options={opts} />}
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-dot" />
      <div className="typing-dot" />
      <div className="typing-dot" />
    </div>
  )
}

export default function MessageBubble({ message }) {
  const { role, text, data } = message
  const isUser = role === 'user'
  const isBot = role === 'bot'
  const sources = data?.sources || []

  // Perplexity-style horizontal source chips
  const SourcesHeader = () => {
    if (!isBot || sources.length === 0) return null
    
    // Deduplicate by URL or title
    const uniqueSources = Array.from(new Map(sources.map(s => [s.url || s, s])).values())

    return (
      <div className="sources-container" style={{ 
        display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '16px', 
        marginBottom: '16px', borderBottom: '1px solid var(--border-subtle)',
        scrollbarWidth: 'none'
      }}>
        {uniqueSources.map((s, idx) => {
          const title = typeof s === 'string' ? s : s.title
          const url = typeof s === 'string' ? '#' : s.url
          return (
            <a key={idx} href={url} target="_blank" rel="noopener noreferrer" 
               className="source-chip"
               style={{ 
                 display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', 
                 background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', 
                 borderRadius: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', 
                 textDecoration: 'none', whiteSpace: 'nowrap', transition: 'all 0.2s' 
               }}>
              <div style={{ 
                width: 16, height: 16, borderRadius: '4px', background: 'var(--accent-primary)', 
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' 
              }}>
                <Globe size={10} />
              </div>
              <span style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</span>
              <ExternalLink size={10} style={{ opacity: 0.5 }} />
            </a>
          )
        })}
      </div>
    )
  }

  return (
    <div className={`message-wrapper ${role}`}>
      <div className="message-inner">
        <div className={`avatar ${role}`}>
          {isUser ? <User size={18} /> : <Sparkles size={18} color="#10a37f" />}
        </div>
        <div className="bubble">
          {isBot && <SourcesHeader />}

          {data?.intent && !isUser && (
            <span className="intent-tag" style={{ marginBottom: '12px' }}>
              <CheckCircle2 size={10} style={{ marginRight: 4 }} />
              Analysis: {data.intent.replace(/_/g, ' ').toUpperCase()}
            </span>
          )}
          
          <div className="markdown-content">
            <ReactMarkdown>{data?.answer || text}</ReactMarkdown>
          </div>
          
          {data?.key_metrics && Object.keys(data.key_metrics).length > 0 && (
            <div className="metrics-row">
              {Object.entries(data.key_metrics).map(([k, v]) => (
                <div key={k} className="metric-card">
                  <div className="metric-label">{k.replace(/_/g, ' ')}</div>
                  <div className="metric-value">{typeof v === 'number' ? 
                     (k.includes('pct') || k.includes('percentage') ? v.toFixed(1) + '%' : '€' + v.toLocaleString()) 
                     : v}</div>
                </div>
              ))}
            </div>
          )}

          {data?.chart_data && <ChartPanel chartData={data.chart_data} />}
        </div>
      </div>
    </div>
  )
}
