'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import {
  Search, TrendingUp, TrendingDown,
  AlertTriangle, Loader2, BarChart3,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import KLineChart from '@/components/KLineChart'
import AnalysisView from '@/components/AnalysisView'
import SystemStatusBar from '@/components/SystemStatusBar'
import MockWarningBanner from '@/components/MockWarningBanner'
import LimitUpCard from '@/components/LimitUpCard'
import LimitDownCard from '@/components/LimitDownCard'
import AITooltip from '@/components/AITooltip'
import AppHeader from '@/components/AppHeader'
import { API_BASE, api } from '@/lib/api'
import { useSystemStatus } from '@/components/SystemStatusProvider'
import type { StockScores } from '@/lib/types'
import { capitalStageColor, confidenceColor } from '@/lib/types'

export default function StockPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    }>
      <StockPageContent />
    </Suspense>
  )
}

interface StockSummary {
  symbol: string
  name: string
  close: number
  pct_change: number
  volume: number
  turnover: number
  high: number
  low: number
  market_cap?: number
  pe?: number
  open?: number
  prev_close?: number
}

interface KLineRecord {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  [key: string]: any
}

interface AnalysisResult {
  summary: StockSummary
  analysis: string
  data_points: number
  kline_data?: KLineRecord[]
  is_mock_data?: boolean
  is_degraded?: boolean
}

const navLinks = [
  { href: '/', label: '首页' },
  { href: '/market', label: '大盘' },
  { href: '/review', label: '复盘' },
  { href: '/workbench', label: '工作台' },
  { href: '/backtest', label: '回测' },
  { href: '/strategies', label: '策略' },
]

function StockPageContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const symbol = searchParams.get('symbol') || ''

  const [inputSymbol, setInputSymbol] = useState(symbol)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [scores, setScores] = useState<StockScores | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [limitUpResult, setLimitUpResult] = useState<any>(null)
  const [limitDownResult, setLimitDownResult] = useState<any>(null)
  const { isMock } = useSystemStatus()

  useEffect(() => {
    if (symbol) fetchAnalysis(symbol)
  }, [symbol])

  const fetchAnalysis = async (code: string) => {
    setLoading(true)
    setError('')
    setResult(null)
    setLimitUpResult(null)
    setLimitDownResult(null)
    try {
      const aiRes = await fetch(`${API_BASE}/api/analysis/stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: code, analysis_type: 'comprehensive' }),
      })
      let data: AnalysisResult
      if (aiRes.ok) {
        data = await aiRes.json()
      } else {
        const fallback = await fetch(`${API_BASE}/api/analysis/local-analysis`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: code, analysis_type: 'comprehensive' }),
        })
        if (!fallback.ok) {
          const err = await fallback.json()
          throw new Error(err.detail || '分析失败')
        }
        data = await fallback.json()
      }
      setResult(data)

      try {
        const sc = await api.getStockScores({ symbol: code })
        setScores(sc)
      } catch { setScores(null) }

      const [upRes, downRes] = await Promise.all([
        fetch(`${API_BASE}/api/analysis/limit-up`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: code }),
        }),
        fetch(`${API_BASE}/api/analysis/limit-down`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: code }),
        }),
      ])
      if (upRes.ok) setLimitUpResult(await upRes.json())
      if (downRes.ok) setLimitDownResult(await downRes.json())
    } catch (e: any) {
      setError(e.message || '请求失败，请确认后端服务已启动')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputSymbol.trim()) return
    router.push(`/stock?symbol=${inputSymbol.trim()}`)
  }

  const formatPrice = (v: number) => v?.toFixed(2) ?? '--'
  const formatVol = (v: number) => {
    if (!v) return '--'
    if (v > 1e8) return (v / 1e8).toFixed(2) + '亿'
    if (v > 1e4) return (v / 1e4).toFixed(2) + '万'
    return v.toFixed(0)
  }

  return (
    <div className="min-h-screen">
      <AppHeader
        title="AStock"
        icon={
          <div className="w-6 h-6 rounded bg-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground">
            A
          </div>
        }
        showBack
        backHref="/"
        navItems={navLinks.filter(l => l.href !== '/')}
        statusBar={<SystemStatusBar />}
      />

      <main className="max-w-4xl mx-auto px-4 pt-6 pb-8">
        {/* Search bar */}
        <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              value={inputSymbol}
              onChange={(e) => setInputSymbol(e.target.value)}
              placeholder="输入股票代码"
              className="pl-8 h-9 text-xs"
            />
          </div>
          <Button type="submit" size="sm" className="h-9 text-xs">分析</Button>
        </form>

        {loading && (
          <div className="flex flex-col items-center justify-center py-32">
            <Loader2 className="w-6 h-6 animate-spin text-primary mb-3" />
            <p className="text-xs text-muted-foreground">正在分析数据...</p>
          </div>
        )}

        {error && (
          <Card className="border-destructive/20">
            <CardContent className="p-5 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-medium mb-0.5">分析出错</p>
                <p className="text-xs text-muted-foreground">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {result && !loading && (
          <div className="space-y-5">
            {result.is_mock_data && <MockWarningBanner />}

            {/* 摘要卡片 */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <AITooltip symbol={symbol} query="comprehensive">
                        <h1 className="text-lg font-bold cursor-help hover:text-primary transition-colors">
                          {result.summary.name}
                        </h1>
                      </AITooltip>
                      <span className="text-xs text-muted-foreground">{result.summary.symbol}</span>
                      {result.is_mock_data && (
                        <Badge variant="outline" className="text-amber-500 border-amber-500/40 text-[10px]">模拟</Badge>
                      )}
                    </div>
                    <div className="flex items-baseline gap-3">
                      <span className="text-2xl font-bold tracking-tight font-mono">
                        {formatPrice(result.summary.close)}
                      </span>
                      <span className={`text-sm font-medium font-mono ${result.summary.pct_change >= 0 ? 'text-up' : 'text-down'}`}>
                        {result.summary.pct_change >= 0 ? '+' : ''}{result.summary.pct_change.toFixed(2)}%
                      </span>
                      <Badge variant={result.summary.pct_change >= 0 ? 'up' : 'down'} className="text-[10px] px-2 py-0">
                        {result.summary.pct_change >= 0 ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                        {result.summary.pct_change >= 0 ? '上涨' : '下跌'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-4 md:grid-cols-7 gap-3 text-xs">
                  <DataItem label="最高" value={formatPrice(result.summary.high)} valueClass={result.summary.high > result.summary.close ? 'text-up' : 'text-down'} />
                  <DataItem label="最低" value={formatPrice(result.summary.low)} valueClass={result.summary.low < result.summary.close ? 'text-down' : 'text-up'} />
                  <DataItem label="今开" value={formatPrice(result.summary.open ?? 0)} />
                  <DataItem label="昨收" value={formatPrice(result.summary.prev_close ?? 0)} />
                  <DataItem label="成交量" value={formatVol(result.summary.volume)} />
                  <DataItem label="换手率" value={result.summary.turnover?.toFixed(2) + '%'} />
                  <DataItem label="市值" value={result.summary.market_cap ? (result.summary.market_cap / 1e8).toFixed(1) + '亿' : '--'} />
                </div>
              </CardContent>
            </Card>

            {/* 涨停/跌停/预期差 */}
            {limitUpResult?.analysis?.is_limit_up && (
              <LimitUpCard analysis={limitUpResult.analysis} symbol={limitUpResult.symbol} name={limitUpResult.name} />
            )}
            {limitDownResult?.analysis?.is_limit_down && (
              <LimitDownCard analysis={limitDownResult.analysis} symbol={limitDownResult.symbol} name={limitDownResult.name} />
            )}

            {/* K线 */}
            <KLineChart
              symbol={symbol}
              name={result.summary.name}
              isMock={result.is_mock_data || isMock}
              phase={
                scores?.main_capital?.stage === '主升' ? 'zhupan' :
                scores?.main_capital?.stage === '吸筹' ? 'xichou' :
                scores?.main_capital?.stage === '洗盘' ? 'xipan' :
                scores?.main_capital?.stage === '出货' ? 'chuhuo' : 'unknown'
              }
              apiBase={API_BASE}
            />

            {/* 评分 + AI 分析 */}
            {result.is_degraded ? (
              <Card className="border-amber-500/20">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <CardTitle className="text-sm">系统状态</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <AnalysisView text={result.analysis} />
                </CardContent>
              </Card>
            ) : (
              <>
                {scores && <ScoreCard scores={scores} />}
                <AnalysisView text={result.analysis} />
              </>
            )}

            <div className="text-center text-[10px] text-muted-foreground pb-6">
              {result.is_mock_data
                ? '当前无法获取真实行情数据，系统已降级'
                : `基于 ${result.data_points} 个交易日数据 · 不构成投资建议`}
            </div>
          </div>
        )}

        {!symbol && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-32 text-muted-foreground">
            <BarChart3 className="w-10 h-10 mb-3 opacity-30" />
            <p className="text-xs">输入股票代码开始分析</p>
          </div>
        )}
      </main>
    </div>
  )
}

function DataItem({ label, value, valueClass }: { label: string; value: string; valueClass?: string }) {
  return (
    <div>
      <div className="text-[10px] text-muted-foreground mb-0.5">{label}</div>
      <div className={`text-xs font-medium font-mono ${valueClass ?? 'text-foreground/90'}`}>{value}</div>
    </div>
  )
}

function ScoreCard({ scores }: { scores: StockScores }) {
  const { main_capital, technical, composite } = scores
  return (
    <Card className="border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary" />
          <CardTitle className="text-sm">综合评分</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-3 rounded bg-accent/20">
          <span className="text-xs text-muted-foreground">综合评分</span>
          <span className="text-xl font-bold font-mono" style={{
            color: composite >= 60 ? 'hsl(var(--up))' : composite >= 30 ? '#F0883E' : 'hsl(var(--down))'
          }}>{composite}<span className="text-xs text-muted-foreground">/100</span></span>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-muted-foreground">主力行为</span>
            <Badge style={{
              background: capitalStageColor(main_capital.stage) + '22',
              color: capitalStageColor(main_capital.stage)
            }} className="text-[10px]">{main_capital.stage}</Badge>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{
                width: `${main_capital.score}%`,
                background: capitalStageColor(main_capital.stage),
              }} />
            </div>
            <span className="text-[11px] font-mono text-muted-foreground">{main_capital.score}</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-2">{main_capital.advice}</p>
          {main_capital.factors?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {main_capital.factors.map((f, i) => (
                <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-muted text-muted-foreground">{f}</span>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="text-[10px] text-muted-foreground mb-2">技术面</div>
          <div className="space-y-2">
            {[
              { label: '趋势', score: technical.trend_score, max: 40 },
              { label: '量能', score: technical.volume_score, max: 30 },
              { label: '位置', score: technical.position_score, max: 30 },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground w-6">{item.label}</span>
                <div className="flex-1 h-1 rounded-full bg-muted overflow-hidden">
                  <div className="h-full rounded-full" style={{
                    width: `${(item.score / item.max) * 100}%`,
                    background: 'hsl(220, 100%, 65%)',
                  }} />
                </div>
                <span className="text-[11px] font-mono text-muted-foreground">{item.score}</span>
              </div>
            ))}
          </div>
          {technical.factors?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {technical.factors.map((f, i) => (
                <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-muted text-muted-foreground">{f}</span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-[10px] text-muted-foreground">
          <span>置信度</span>
          <span className="px-2 py-0.5 rounded text-[10px]" style={{
            background: confidenceColor(main_capital.confidence) + '22',
            color: confidenceColor(main_capital.confidence),
          }}>{main_capital.confidence}</span>
        </div>
      </CardContent>
    </Card>
  )
}



