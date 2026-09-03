import React, { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import AnalysisPage from './pages/AnalysisPage'
import ChartView from './components/ChartView'
import { getQuote } from './services/api'

const FOREX_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP', 'GBPJPY']
const COMMODITIES = ['XAUUSD', 'XAGUSD', 'WTI', 'BRENT', 'NATGAS', 'COPPER']

export default function App() {
  const [symbol, setSymbol] = useState('EURUSD')
  const [marketType, setMarketType] = useState('forex')
  const [timeframe, setTimeframe] = useState('H4')
  const [quote, setQuote] = useState(null)
  const [watchlist, setWatchlist] = useState([])

  // A list of watch items combining defaults + user watchlist
  const defaultWatch = FOREX_PAIRS.map(s => ({ symbol: s, market_type: 'forex' }))
    .concat(COMMODITIES.map(s => ({ symbol: s, market_type: 'commodity' })))

  const refreshQuote = async () => {
    try {
      const q = await getQuote(symbol, marketType)
      setQuote(q)
    } catch (e) {
      setQuote(null)
    }
  }

  useEffect(() => {
    refreshQuote()
  }, [symbol, marketType])

  return (
    <div className="app">
      <Sidebar
        items={watchlist.length ? watchlist : defaultWatch}
        current={symbol}
        onSelect={(s, t) => { setSymbol(s); setMarketType(t) }}
        onReload={refreshQuote}
      />
      <div className="main">
        <div className="topbar">
          <select value={marketType} onChange={(e) => setMarketType(e.target.value)}>
            <option value="forex">Forex</option>
            <option value="commodity">Commodity</option>
          </select>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {(marketType === 'forex' ? FOREX_PAIRS : COMMODITIES).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            {['M5', 'M15', 'H1', 'H4', 'D1', 'W1'].map(t => <option key={t}>{t}</option>)}
          </select>
          {quote && (
            <div style={{ marginLeft: 'auto', fontSize: 13, color: 'var(--muted)' }}>
              <span className="mono">${quote.price?.toFixed(4)}</span>
            </div>
          )}
        </div>
        <AnalysisPage symbol={symbol} marketType={marketType} timeframe={timeframe} />
      </div>
    </div>
  )
}
