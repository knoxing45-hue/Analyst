import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const runAnalysis = (payload) =>
  api.post('/analysis/analyze', payload).then((r) => r.data)

export const getQuote = (symbol, market_type = 'forex') =>
  api.get(`/market/${encodeURIComponent(symbol)}/quote`, { params: { market_type } }).then((r) => r.data)

export const getHistorical = (symbol, market_type = 'forex', timeframe = 'H4', limit = 100) =>
  api.get(`/market/${encodeURIComponent(symbol)}/historical`, { params: { market_type, timeframe, limit } }).then((r) => r.data)

export const calcRiskReward = (payload) =>
  api.post('/trade/calculate-risk-reward', payload).then((r) => r.data)

export const getWatchlist = () => api.get('/watchlist').then((r) => r.data)
export const addToWatchlist = (payload) => api.post('/watchlist', payload).then((r) => r.data)
export const removeFromWatchlist = (symbol) => api.delete(`/watchlist/${encodeURIComponent(symbol)}`).then((r) => r.data)
export const getHistory = () => api.get('/analysis/history').then((r) => r.data)

export default api
