import React, { useEffect, useRef } from 'react'
import { getHistorical } from '../services/api'

// Rendering a candle chart. We use TradingView's open-source Lightweight Charts
// loaded from CDN for a lightweight, dependency-free chart that mirrors the
// technical analysis displayed in the panel.
export default function ChartView({ symbol, marketType, timeframe }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    const render = async () => {
      try {
        const { candles } = await getHistorical(symbol, marketType, timeframe, 120)
        if (cancelled) return

        const TradingView = window.LightweightCharts
        if (!TradingView) return

        if (!chartRef.current && containerRef.current) {
          const chart = TradingView.createChart(containerRef.current, {
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
            layout: {
              background: { type: 'solid', color: '#171a23' },
              textColor: '#8b91a3',
              fontFamily: 'ui-monospace, monospace',
            },
            grid: { vertLines: { color: '#1e2230' }, horzLines: { color: '#1e2230' } },
            timeScale: { timeVisible: true, secondsVisible: false },
            rightPriceScale: { borderColor: '#2a2f3f' },
          })
          chartRef.current = chart
          seriesRef.current = chart.addCandlestickSeries({
            upColor: '#22c55e', downColor: '#ef4444',
            borderUpColor: '#22c55e', borderDownColor: '#ef4444',
            wickUpColor: '#22c55e', wickDownColor: '#ef4444',
          })
          chart.timeScale().fitContent()
        }

        const data = candles
          .filter((c) => c.timestamp && c.open != null)
          .map((c) => ({
            time: Math.floor(new Date(c.timestamp).getTime() / 1000),
            open: c.open, high: c.high, low: c.low, close: c.close,
          }))
          .sort((a, b) => a.time - b.time)

        seriesRef.current?.setData(data)
      } catch (e) {
        // Live chart is optional; analysis works without it.
      }
    }

    render()
    return () => { cancelled = true }
  }, [symbol, marketType, timeframe])

  return <div ref={containerRef} className="chart-wrap" />
}
