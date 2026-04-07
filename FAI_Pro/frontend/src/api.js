// api.js — Axios API client for IrishHome.AI
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8001',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

export const checkHealth = () => api.get('/health')

export const fetchCounties = () => api.get('/api/meta/counties')

export const fetchYears = () => api.get('/api/meta/years')

export const sendChat = (query, sessionId = null) =>
  api.post('/api/chat', { query, session_id: sessionId })
