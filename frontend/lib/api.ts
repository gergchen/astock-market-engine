/** 统一 API 配置 + 类型化客户端 */

import type { MarketScores, StockScores, StockScoresQuery, SystemStatusResponse } from "./types"

const DEFAULT_PORT = "8005"

const getApiBase = () => {
  // 1. 环境变量（构建时注入）
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL
  }
  // 2. 运行时动态 hostname（支持局域网访问）
  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:${DEFAULT_PORT}`
  }
  // 3. SSR fallback
  return `http://127.0.0.1:${DEFAULT_PORT}`
}

export const API_BASE = getApiBase()

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  getMarketScores(): Promise<MarketScores> {
    return fetchJSON<MarketScores>("/api/analysis/market-scores")
  },

  getStockScores(query: StockScoresQuery): Promise<StockScores> {
    return fetchJSON<StockScores>("/api/analysis/stock-scores", {
      method: "POST",
      body: JSON.stringify(query),
    })
  },

  getMarketReview(): Promise<{
    market_scores: MarketScores
    limit_up_count: number
    limit_down_count: number
    zhaban_rate: number
    ai_review: string
  }> {
    return fetchJSON("/api/analysis/market-review")
  },

  getEmotionCycle(): Promise<{
    emotion_score: number
    emotion_stage: string
    confidence: string
    signals: string[]
    suggestion: string
  }> {
    return fetchJSON("/api/analysis/emotion-cycle")
  },

  getDragonLeaders(): Promise<Record<string, unknown>> {
    return fetchJSON("/api/analysis/dragon-leaders")
  },

  getSectorRotation(): Promise<Record<string, unknown>> {
    return fetchJSON("/api/analysis/sector-rotation")
  },

  getSystemStatus(): Promise<SystemStatusResponse> {
    return fetchJSON<SystemStatusResponse>("/api/stock/system/status")
  },
}
