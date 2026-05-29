/** 前后端契约 — 与 backend/schemas/*.py 同步
 *
 * 变更时记得同步更新后端 Pydantic 模型。
 * 也可通过 openapi-typescript 从 /openapi.json 自动生成。
 */

// ── 市场评分 ──

export interface EmotionScores {
  score: number               // 0-100，主升期最高
  stage: string               // 冰点期|修复期|主升期|高潮期|分歧期|退潮期
  confidence: "高" | "中" | "低"
  all_stage_scores: Record<string, number>
  signals: string[]
  suggestion: string
}

export interface DragonIntensity {
  score: number               // 0-100
  top_leader_score: number
  high_board_count: number
  top_leaders: Array<{
    name: string
    boards: number
    industry: string
  }>
}

export interface RiskScores {
  score: number               // 0-100，越高越危险
  level: "低" | "中" | "高" | "极高"
  factors: string[]
}

export interface MarketScores {
  emotion: EmotionScores
  dragon_intensity: DragonIntensity
  risk: RiskScores
  computed_at: string
}

// ── 个股评分 ──

export interface MainCapitalScores {
  score: number               // 0-100，主升=90，出货=15
  stage: string               // 吸筹|洗盘|主升|出货
  confidence: "高" | "中" | "低"
  all_stage_scores: Record<string, number>
  factors: string[]
  advice: string
}

export interface TechnicalScores {
  score: number               // 0-100
  trend_score: number         // 0-40
  volume_score: number        // 0-30
  position_score: number      // 0-30
  factors: string[]
}

export interface StockScores {
  symbol: string
  name: string
  main_capital: MainCapitalScores
  technical: TechnicalScores
  composite: number           // 0-100
}

// ── 请求 ──

export interface StockScoresQuery {
  symbol: string
}

// ── 评分颜色映射（前端可视化用）──

export function emotionColor(stage: string): string {
  const map: Record<string, string> = {
    "冰点期": "#3b82f6", "修复期": "#22c55e", "主升期": "#ef4444",
    "高潮期": "#f97316", "分歧期": "#eab308", "退潮期": "#6b7280",
  }
  return map[stage] ?? "#6b7280"
}

export function riskColor(level: string): string {
  const map: Record<string, string> = {
    "低": "#22c55e", "中": "#eab308", "高": "#f97316", "极高": "#ef4444",
  }
  return map[level] ?? "#6b7280"
}

export function confidenceColor(conf: string): string {
  const map: Record<string, string> = {
    "高": "#22c55e", "中": "#eab308", "低": "#6b7280",
  }
  return map[conf] ?? "#6b7280"
}

export function capitalStageColor(stage: string): string {
  const map: Record<string, string> = {
    "主升": "#ef4444", "吸筹": "#22c55e", "洗盘": "#3b82f6", "出货": "#6b7280",
  }
  return map[stage] ?? "#6b7280"
}

// ── 数据质量类型 ──

export interface QualityInfo {
  source: string
  confidence: number
  realtime: boolean
  fallback_used: boolean
}

export type SystemStatusType = "realtime" | "cache" | "stale" | "mock" | "unknown"

export interface SystemStatusResponse {
  status: SystemStatusType
  sources: Array<{
    name: string
    source: string
    confidence: number
    realtime: boolean
    fallback_used: boolean
  }>
  updated_at: string
}
