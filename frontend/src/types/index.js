// Shared type definitions mirroring the backend contracts.

/**
 * @typedef {Object} AnalysisRequest
 * @property {string} symbol
 * @property {'forex'|'commodity'} market_type
 * @property {string} timeframe
 * @property {number} account_size
 * @property {number} risk_percent
 * @property {'lots'|'%account'|'units'} sizing_pref
 */

/**
 * @typedef {Object} AnalysisResult
 * @property {string} symbol
 * @property {string} ticker
 * @property {string} market_type
 * @property {string} timeframe
 * @property {number} current_price
 * @property {Object} quote
 * @property {Object} indicators
 * @property {Object} structure
 * @property {string|null} ai_output
 * @property {Object} analysis
 * @property {Object} trade_setup
 * @property {number} confidence
 * @property {boolean} mock
 */

/** @typedef {Object} TradeSet - target ladder element */
export {}
