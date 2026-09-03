import React from 'react'

// Compact watchlist sidebar. Shows symbol, price if available (from backend quote
// is lazily fetched by parent, so we show symbol + market type here).
export default function Sidebar({ items, current, onSelect, onReload }) {
  return (
    <aside className="sidebar">
      <h2>Market Watchlist</h2>
      {items.map((it, i) => (
        <div
          key={it.symbol + i}
          className="watch-item"
          style={it.symbol === current ? { borderColor: 'var(--blue)' } : undefined}
          onClick={() => onSelect(it.symbol, it.market_type)}
        >
          <div className="sym">{it.symbol}</div>
          <div className="px">{it.market_type}</div>
        </div>
      ))}
      <h2>Controls</h2>
      <button onClick={onReload} className="primary" style={{ width: '100%' }}>
        Refresh Quote
      </button>
    </aside>
  )
}
