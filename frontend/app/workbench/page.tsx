'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  RefreshCw, TrendingUp, TrendingDown,
  Activity, BarChart3, Crown, AlertTriangle, Calendar, ExternalLink,
} from 'lucide-react'
import EmotionTimeline from '@/components/EmotionTimeline'
import DragonTree from '@/components/DragonTree'
import ZhabanHeatmap from '@/components/ZhabanHeatmap'
import AppHeader from '@/components/AppHeader'
import { API_BASE, api } from '@/lib/api'
import { Spinner, ErrorState, EmptyState, SkeletonCard } from '@/components/ui/states'
import type { MarketScores } from '@/lib/types'
import { emotionColor, riskColor } from '@/lib/types'

/* ─── hooks ─── */
function usePolling<T>(fetcher: () => Promise<T>, interval = 60000) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const doFetch = useCallback(async () => {
    try {
      const r = await fetcherRef.current()
      setData(r)
      setError('')
    } catch (e: any) {
      console.error('[Workbench] fetch error:', e)
      setError(e?.message || String(e) || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    doFetch()
    const t = setInterval(doFetch, interval)
    return () => clearInterval(t)
  }, [doFetch, interval])

  return { data, loading, error, refetch: doFetch }
}

/* ─── 状态栏 ─── */
function StatusBar({ scores }: { scores: MarketScores | null }) {
  if (!scores) return null
  const items = [
    { label: '情绪', value: scores.emotion.stage, color: emotionColor(scores.emotion.stage), score: scores.emotion.score },
    { label: '龙头', value: '活跃度', color: '#F0883E', score: scores.dragon_intensity.score },
    { label: '风险', value: scores.risk.level, color: riskColor(scores.risk.level), score: scores.risk.score },
  ]
  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded border border-border bg-card">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="flex flex-col">
            <span className="text-[10px] text-muted-foreground">{it.label}</span>
            <span className="text-xs font-semibold" style={{ color: it.color }}>{it.value}</span>
          </div>
          <div className="w-7 h-7 rounded flex items-center justify-center text-[11px] font-bold font-mono"
            style={{ background: it.color + '12', color: it.color }}>{it.score}</div>
          {i < items.length - 1 && <div className="w-px h-6 bg-border" />}
        </div>
      ))}
    </div>
  )
}

/* ─── 数据卡 ─── */
function DataCard({ label, value, sub, icon, color, trend }: {
  label: string; value: string | number; sub?: string; icon: React.ReactNode; color?: string; trend?: 'up' | 'down' }) {
  return (
    <div className="p-4 rounded border border-border bg-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] text-muted-foreground tracking-wide uppercase mb-1">{label}</p>
          <p className="text-xl font-bold tracking-tight font-mono" style={{ color }}>
            {value}
          </p>
          {sub && <p className="text-[10px] text-muted-foreground mt-0.5">{sub}</p>}
        </div>
        <div className="w-7 h-7 rounded flex items-center justify-center"
          style={{ background: (color || 'hsl(var(--primary))') + '10' }}>
          {icon}
        </div>
      </div>
      {trend && (
        <div className={`mt-2 text-[10px] ${trend === 'up' ? 'text-up' : 'text-down'}`}>
          {trend === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        </div>
      )}
    </div>
  )
}

/* ─── 主页 ─── */
export default function WorkbenchPage() {
  const router = useRouter()

  const { data: dragonData, loading: dLoad, error: dErr, refetch: refD } = usePolling(async () => {
    const res = await fetch(`${API_BASE}/api/analysis/dragon-leaders`, { method: 'POST' })
    return res.ok ? res.json() : null
  })

  const { data: scores, loading: sLoad, error: sErr, refetch: refS } = usePolling(async () => {
    return api.getMarketScores()
  })

  const isLoading = dLoad || sLoad

  return (
    <div className="min-h-screen">
      <AppHeader
        title="工作台"
        icon={<Activity className="w-4 h-4 text-muted-foreground" />}
        navItems={[
          { href: '/market', label: '大盘' },
          { href: '/review', label: '复盘' },
          { href: '/backtest', label: '回测' },
        ]}
        onRefresh={() => { refD(); refS() }}
        isRefreshing={isLoading}
      />

      <main className="max-w-7xl mx-auto px-5 py-5 space-y-5">
        {isLoading ? (
          <div className="space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[...Array(4)].map((_, i) => <SkeletonCard key={i} lines={2} />)}
            </div>
            <SkeletonCard lines={3} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <SkeletonCard lines={6} /><SkeletonCard lines={4} />
            </div>
          </div>
        ) : dErr ? (
          <ErrorState message={'加载失败: ' + dErr} onRetry={() => { refD(); refS() }} />
        ) : (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <StatusBar scores={scores} />
              <span className="text-[10px] text-muted-foreground flex items-center gap-1.5">
                <Calendar className="w-3 h-3" />
                {new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <DataCard label="市场情绪" value={scores?.emotion.stage || '--'}
                sub={scores ? '置信度 ' + scores.emotion.confidence : undefined}
                icon={<Activity className="w-3.5 h-3.5" />}
                color={scores ? emotionColor(scores.emotion.stage) : undefined} />
              <DataCard label="龙头强度" value={scores?.dragon_intensity.score ?? '--'}
                sub={scores ? scores.dragon_intensity.high_board_count + ' 只高标' : undefined}
                icon={<Crown className="w-3.5 h-3.5" />} color="#F0883E" />
              <DataCard label="风险等级" value={scores?.risk.level ?? '--'}
                sub={scores?.risk.factors?.[0]}
                icon={<AlertTriangle className="w-3.5 h-3.5" />}
                color={scores ? riskColor(scores.risk.level) : undefined} />
              <DataCard label="涨停 / 炸板" value={dragonData?.market_summary?.涨停数 ?? '--'}
                sub={dragonData?.market_summary ? '最高' + dragonData.market_summary.最高板 + '板' : undefined}
                icon={<BarChart3 className="w-3.5 h-3.5" />} color="#D94040" trend="up" />
            </div>

            <EmotionTimeline limit={30} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {dragonData?.leaders?.length ? <DragonTree data={dragonData} />
                : <EmptyState type="no_data" message={dragonData ? '暂无龙头数据' : '龙头数据加载中…'} />}
              <ZhabanHeatmap />
            </div>

            <div className="flex items-center gap-2 justify-center pt-1">
              <button onClick={() => router.push('/market')}
                className="flex items-center gap-1.5 px-3 py-2 rounded bg-muted text-xs text-muted-foreground hover:text-foreground transition-colors">
                <Activity className="w-3 h-3" />大盘概况<ExternalLink className="w-2.5 h-2.5 opacity-40" />
              </button>
              <button onClick={() => router.push('/review')}
                className="flex items-center gap-1.5 px-3 py-2 rounded bg-muted text-xs text-muted-foreground hover:text-foreground transition-colors">
                <Calendar className="w-3 h-3" />市场复盘<ExternalLink className="w-2.5 h-2.5 opacity-40" />
              </button>
            </div>

            <div className="text-center text-[10px] text-muted-foreground/40 pb-6 pt-1">
              数据基于 akshare · 不构成投资建议
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
