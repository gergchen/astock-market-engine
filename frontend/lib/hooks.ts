/** SWR hooks — 统一数据获取层 */

import useSWR, { type SWRConfiguration } from 'swr'
import { API_BASE, api } from './api'

const fetcher = (url: string) => fetch(url).then(r => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
})

const postFetcher = ([url, body]: [string, unknown]) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  })

const defaultOpts: SWRConfiguration = {
  revalidateOnFocus: false,
  dedupingInterval: 30000,
}

// ── 市场数据 ──

export function useMarketOverview() {
  return useSWR(`${API_BASE}/api/stock/market-overview`, fetcher, defaultOpts)
}

export function useMarketScores() {
  return useSWR(`${API_BASE}/api/analysis/market-scores`, fetcher, {
    ...defaultOpts,
    refreshInterval: 60000,
  })
}

export function useSectorFlow() {
  return useSWR(`${API_BASE}/api/stock/sector-flow`, fetcher, defaultOpts)
}

export function useEmotionCycle() {
  return useSWR(`${API_BASE}/api/analysis/emotion-cycle`, fetcher, defaultOpts)
}

// ── 个股数据 ──

export function useStockDaily(symbol: string) {
  return useSWR(
    symbol ? `${API_BASE}/api/analysis/kline/${symbol}` : null,
    fetcher,
    { ...defaultOpts, refreshInterval: 60000 }
  )
}

export function useStockScores(symbol: string) {
  return useSWR(
    symbol ? [`${API_BASE}/api/analysis/stock-scores`, { symbol }] : null,
    postFetcher,
    defaultOpts
  )
}

// ── 复盘 / 龙头 ──

export function useMarketReview() {
  return useSWR(`${API_BASE}/api/analysis/market-review`, fetcher, defaultOpts)
}

export function useDragonLeaders() {
  return useSWR([`${API_BASE}/api/analysis/dragon-leaders`, {}], postFetcher, defaultOpts)
}

export function useSectorRotation() {
  return useSWR(`${API_BASE}/api/analysis/sector-rotation`, fetcher, defaultOpts)
}

export function useSimilarToday() {
  return useSWR(`${API_BASE}/api/analysis/rag/similar-today`, fetcher, defaultOpts)
}

// ── 系统状态 ──

export function useSystemStatus() {
  return useSWR(`${API_BASE}/api/stock/system/status`, fetcher, {
    ...defaultOpts,
    refreshInterval: 30000,
  })
}

// ── 策略 ──

export function useStrategyMarket(sortBy: string = 'sharpe') {
  return useSWR(`${API_BASE}/api/analysis/strategy-market?sort_by=${sortBy}`, fetcher, defaultOpts)
}
