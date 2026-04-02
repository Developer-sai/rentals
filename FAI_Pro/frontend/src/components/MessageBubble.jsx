import { useEffect } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, RadialLinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'
import { Bar, Line, Doughnut, PolarArea, Radar } from 'react-chartjs-2'
import ReactMarkdown from 'react-markdown'

ChartJS.register(
  CategoryScale, LinearScale, RadialLinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  animation: { duration: 400 },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#2f2f2f', titleColor: '#fff', bodyColor: '#ececec',
      padding: 8, borderColor: '#383838', borderWidth: 1
    },
  },
  scales: {
    x: { grid: { color: 'rgba(128,128,128,0.1)' }, ticks: { font: { family: 'Inter' } } },
    y: { grid: { color: 'rgba(128,128,128,0.1)' }, ticks: { font: { family: 'Inter' } } },
  },
}

function ChartPanel({ chartData }) {
  if (!chartData) return null
  const { type, labels, values, title } = chartData
  const THEME_BLUE = '#10a37f'
  
  const dataset = {
    labels,
    datasets: [{
      label: title, data: values,
      backgroundColor: type === 'doughnut' || type === 'polarArea' || type === 'radar' 
        ? ['#10a37f', '#2a5b51', '#3b8b78', '#5cc0a9', '#146f59'] 
        : 'rgba(16, 163, 127, 0.4)',
      borderColor: THEME_BLUE,
      borderWidth: 1.5,
      fill: type === 'line' || type === 'radar',
    }],
  }

  const opts = { ...chartOptions }
  if (type === 'doughnut' || type === 'polarArea' || type === 'radar') {
    opts.scales = {}
    opts.plugins.legend = { display: true, position: 'bottom' }
  }

  return (
    <div className="chart-panel">
      <div className="chart-title">{title}</div>
      <div className="chart-wrap">
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

  return (
    <div className={`message-wrapper ${role}`}>
      <div className="message-inner">
        <div className={`avatar ${role}`}>
          {isUser ? 'U' : 'A'}
        </div>
        <div className="bubble">
          {data?.intent && <span className="intent-tag">Intent: {data.intent.replace('_', ' ')}</span>}
          
          <ReactMarkdown>{data?.answer || text}</ReactMarkdown>
          
          {data?.key_metrics && Object.keys(data.key_metrics).length > 0 && (
            <div className="metrics-row">
              {Object.entries(data.key_metrics).map(([k, v]) => (
                <div key={k} className="metric-card">
                  <div className="metric-label">{k.replace(/_/g, ' ').toUpperCase()}</div>
                  <div className="metric-value">{typeof v === 'number' ? 
                     (k.includes('pct') || k.includes('percentage') ? v + '%' : '€' + v.toLocaleString()) 
                     : v}</div>
                </div>
              ))}
            </div>
          )}

          {data?.chart_data && <ChartPanel chartData={data.chart_data} />}
          
          {data?.sources && data.sources.length > 0 && (
            <div className="intent-tag" style={{ marginTop: '16px' }}>
              Sources: {data.sources.join(', ')}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
