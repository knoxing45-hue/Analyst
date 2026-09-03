import React, { useEffect, useState } from 'react'
import ChartView from '../components/ChartView'
import { runAnalysis } from '../services/api'

export default function AnalysisPage({ symbol, marketType, timeframe }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Pass account params; could later be user-configurable.
  const account = { account_size: 10000, risk_percent: 1.0, sizing_pref: 'lots' }

  const analyze = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const r = await runAnalysis({
        symbol, market_type: marketType, timeframe,
        ...account,
        include_news: true,
      })
      setResult(r)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Auto-analyze on symbol/timeframe change for a snappy dashboard feel.
    let active = true
    setLoading(true)
    setError(null)
    runAnalysis({ symbol, market_type: marketType, timeframe, ...account, include_news: true })
      .then((r) => active && setResult(r))
      .catch((e) => active && setError(e.response?.data?.detail || e.message))
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [symbol, marketType, timeframe])

  const t = result?.trade_setup || {}
  const targets = t.targets || []
  const confidence = result?.confidence ?? result?.analysis?.confidence
  const regime = result?.structure?.regime || ''

  return (
    <div className="content">
      <div className="card">
        <h3>Price Chart — {symbol} {timeframe}</h3>
        <ChartView symbol={symbol} marketType={marketType} timeframe={timeframe} />
      </div>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h3 style={{ marginBottom: 0 }}>AI Market Analysis</h3>
          {loading && <div className="loading"><span className="spinner" /> Analyzing…</div>}
        </div>

        {error && <div className="warning">Error: {error}</div>}

        {!result && !loading && !error && (
          <p style={{ color: 'var(--muted)' }}>Click “Analyze” to run a full analysis.</p>
        )}

        {result && (
          <>
            {result.mock && (
              <div className="warning" style={{ marginBottom: 12 }}>
                DeepSeek API key not configured — showing offline mock analysis. Set DEEPSEEK_API_KEY in backend/.env for full AI reasoning.
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 }}>
              <span className={`badge ${regime.includes('up') ? 'green' : regime.includes('down') ? 'red' : 'amber'}`}>
                {regime}
              </span>
              {typeof confidence === 'number' && (
                <span className={`badge ${confidence >= 60 ? 'green' : confidence >= 45 ? 'amber' : 'red'}`}>
                  Confidence {confidence}%
                </span>
              )}
            </div>

            {result.analysis?.executive_summary && (
              <p style={{ color: 'var(--text)', marginBottom: 12 }}>
                {result.analysis.executive_summary}
              </p>
            )}

            <div className="card" style={{ background: 'var(--panel2)' }}>
              <h3>Trade Setup</h3>
              {t.entry != null ? (
                <div className="setup-grid">
                  <div className="setup-item">
                    <div className="lbl">Direction</div>
                    <div className="val" style={{ color: t.direction === 'long' ? 'var(--green)' : 'var(--red)' }}>
                      {t.direction?.toUpperCase()}
                    </div>
                  </div>
                  <div className="setup-item">
                    <div className="lbl">Entry</div>
                    <div className="val mono">{t.entry}</div>
                  </div>
                  <div className="setup-item">
                    <div className="lbl">Stop Loss</div>
                    <div className="val mono" style={{ color: 'var(--red)' }}>{t.stop_loss}</div>
                  </div>
                  <div className="setup-item">
                    <div className="lbl">Position Lots</div>
                    <div className="val mono">{t.position_lots}</div>
                  </div>
                  <div className="setup-item">
                    <div className="lbl">Risk Amount</div>
                    <div className="val mono">${t.risk_amount}</div>
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--muted)' }}>No valid setup generated for this analysis.</p>
              )}

              {targets.length > 0 && (
                <table style={{ marginTop: 12 }}>
                  <thead>
                    <tr><th>Take Profit</th><th>Price</th><th>R:R</th><th>Partial Close</th></tr>
                  </thead>
                  <tbody>
                    {targets.map((tp, i) => (
                      <tr key={i}>
                        <td>TP{i + 1}</td>
                        <td className="mono">{tp.target}</td>
                        <td className="mono">{tp.rr_ratio}</td>
                        <td>{tp.partial_close_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="card" style={{ background: 'var(--panel2)', marginTop: 12 }}>
              <h3>Key Levels</h3>
              {(result.structure?.key_levels || []).map((lv, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ color: 'var(--muted)' }}>{lv.type}</span>
                  <span className="mono">{lv.price}</span>
                </div>
              ))}
              {!result.structure?.key_levels?.length && <p style={{ color: 'var(--muted)' }}>None detected.</p>}
            </div>

            {result.ai_output && (
              <div className="card" style={{ background: 'var(--panel2)', marginTop: 12 }}>
                <h3>DeepSeek Full Analysis</h3>
                <div className="ai-output">{result.ai_output}</div>
              </div>
            )}
          </>
        )}

        <button className="primary" style={{ marginTop: 16 }} onClick={analyze} disabled={loading}>
          {loading ? 'Analyzing…' : 'Run Full Analysis'}
        </button>
      </div>
    </div>
  )
}
