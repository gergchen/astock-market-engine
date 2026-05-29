'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  TrendingUp, TrendingDown, Activity, BarChart3, Loader2,
  Building, Newspaper, FileText,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AppHeader from '@/components/AppHeader'
import DragonLeaderCard from '@/components/DragonLeaderCard'
import SectorRotationCard from '@/components/SectorRotationCard'
import SystemStatusBar from '@/components/SystemStatusBar'
import MockWarningBanner from '@/components/MockWarningBanner'
import { ErrorState, EmptyState } from '@/components/ui/states'
import {
  useMarketOverview, useMarketReview, useSectorFlow,
  useDragonLeaders, useSectorRotation, useMarketScores,
} from '@/lib/hooks'
import { useSystemStatus } from '@/components/SystemStatusProvider'
import type { MarketScores } from '@/lib/types'
import { emotionColor, riskColor } from '@/lib/types'

export default function MarketPage() {
  const router = useRouter()
  const [scrolled, setScrolled] = useState(false)
  const { isMock } = useSystemStatus()

  const { data: overview, error: ovErr } = useMarketOverview()
  const { data: marketReview, error: mrErr } = useMarketReview()
  const { data: sectorData } = useSectorFlow()
  const { data: dragonLeaders } = useDragonLeaders()
  const { data: sectorRotation } = useSectorRotation()
  const { data: marketScores } = useMarketScores()

  const sectorFlow = sectorData?.sectors ?? []
  const loading = !overview && !marketReview && !ovErr && !mrErr
  const error = ovErr && mrErr ? (ovErr?.message || mrErr?.message || '加载失败') : ''

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const getEmotionStyle = (stage: string) => {
    const map: Record<string, { color: string; bg: string }> = {
      '冰点期': { color: 'text-blue-400', bg: 'bg-muted' },
      '修复期': { color: 'text-down', bg: 'bg-muted' },
      '主升期': { color: 'text-up', bg: 'bg-muted' },
      '高潮期': { color: 'text-up', bg: 'bg-muted' },
      '分歧期': { color: 'text-muted-foreground', bg: 'bg-muted' },
      '退潮期': { color: 'text-down', bg: 'bg-muted' },
    }
    return map[stage] || { color: 'text-muted-foreground', bg: 'bg-muted' }
  }

  const emotion = marketReview?.emotion
  const topBoards = marketReview?.top_boards || []
  const zhabanRate = marketReview?.zhaban_rate
  const limitUpCount = marketReview?.limit_up_count ?? 0
  const limitDownCount = marketReview?.limit_down_count ?? 0

  return (
    <div className="min-h-screen bg-background">
      <AppHeader
        title="大盘概况"
        variant="fixed"
        scrolled={scrolled}
        statusBar={<SystemStatusBar />}
        navItems={[
          { href: '/', label: '首页' },
          { href: '/stock?symbol=000001', label: '个股' },
          { href: '/review', label: '复盘' },
        ]}
      />

      <main className="max-w-4xl mx-auto px-4 pt-16 pb-8">
        {loading ? (
          <div className="flex justify-center py-24">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <ErrorState message={`大盘数据加载失败: ${error}`} />
        ) : !overview && !marketReview ? (
          <EmptyState type="no_data" message="暂无大盘数据" />
        ) : (
          <div className="space-y-4">
            {isMock && <MockWarningBanner />}

            {/* 大盘指数 */}
            {overview && (
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: '上证指数', value: overview['上证指数'] },
                  { label: '深证成指', value: overview['深证成指'] },
                  { label: '创业板指', value: overview['创业板指'] },
                  { label: '科创50', value: overview['科创50'] },
                ].filter(i => i.value).map(item => {
                  const v = item.value
                  const pct = parseFloat(v?.涨跌幅 || 0)
                  return (
                    <Card key={item.label} className="border-border rounded">
                      <CardContent className="p-4">
                        <div className="text-[11px] text-muted-foreground mb-1">{item.label}</div>
                        <div className={`text-lg font-bold font-mono ${pct >= 0 ? 'text-up' : 'text-down'}`}>
                          {parseFloat(v?.最新价 || 0).toFixed(2)}
                        </div>
                        <div className={`text-xs font-mono ${pct >= 0 ? 'text-up' : 'text-down'}`}>
                          {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}

            {/* 涨跌停统计 */}
            <div className="grid grid-cols-3 gap-3">
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">涨停</div>
                  <div className="text-2xl font-bold font-mono text-up">{limitUpCount}</div>
                </CardContent>
              </Card>
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">跌停</div>
                  <div className="text-2xl font-bold font-mono text-down">{limitDownCount}</div>
                </CardContent>
              </Card>
              <Card className="border-border rounded">
                <CardContent className="p-4">
                  <div className="text-[11px] text-muted-foreground mb-1">炸板率</div>
                  <div className="text-2xl font-bold font-mono">{zhabanRate != null ? (zhabanRate * 100).toFixed(1) + '%' : '--'}</div>
                </CardContent>
              </Card>
            </div>

            {/* 情绪周期 */}
            {emotion && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">情绪周期</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-2xl font-bold" style={{ color: emotionColor(emotion.stage) }}>
                        {emotion.stage}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        置信度: {emotion.confidence}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="text-xs text-muted-foreground leading-relaxed">
                        {emotion.suggestion}
                      </div>
                    </div>
                  </div>
                  {emotion.signals?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {emotion.signals.map((s: string, i: number) => (
                        <Badge key={i} variant="outline" className="text-[10px]">{s}</Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 市场复盘 */}
            {marketReview?.ai_review && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">市场复盘</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {marketReview.ai_review}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 龙头股 */}
            {dragonLeaders && (
              <DragonLeaderCard data={dragonLeaders} />
            )}

            {/* 板块轮动 */}
            <SectorRotationCard data={sectorRotation} />

            {/* 市场评分 */}
            {marketScores && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">市场评分</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded bg-muted">
                      <div className="text-[10px] text-muted-foreground mb-1">情绪</div>
                      <div className="text-xl font-bold font-mono" style={{ color: emotionColor(marketScores.emotion.stage) }}>
                        {marketScores.emotion.score}
                      </div>
                      <Badge className="text-[10px] mt-1" style={{
                        background: emotionColor(marketScores.emotion.stage) + '18',
                        color: emotionColor(marketScores.emotion.stage),
                        border: 'none',
                      }}>{marketScores.emotion.stage}</Badge>
                    </div>
                    <div className="p-3 rounded bg-muted">
                      <div className="text-[10px] text-muted-foreground mb-1">龙头强度</div>
                      <div className="text-xl font-bold font-mono">{marketScores.dragon_intensity.score}</div>
                      <div className="text-[10px] text-muted-foreground">{marketScores.dragon_intensity.high_board_count} 只高标</div>
                    </div>
                    <div className="p-3 rounded bg-muted">
                      <div className="text-[10px] text-muted-foreground mb-1">风险</div>
                      <div className="text-xl font-bold font-mono" style={{ color: riskColor(marketScores.risk.level) }}>
                        {marketScores.risk.score}
                      </div>
                      <Badge className="text-[10px] mt-1" style={{
                        background: riskColor(marketScores.risk.level) + '18',
                        color: riskColor(marketScores.risk.level),
                        border: 'none',
                      }}>{marketScores.risk.level}风险</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 连板高标 */}
            {topBoards.length > 0 && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">连板高标</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">#</th>
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">代码</th>
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">名称</th>
                          <th className="text-right px-3 py-2 text-muted-foreground font-medium">连板</th>
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">行业</th>
                          <th className="text-right px-3 py-2 text-muted-foreground font-medium">封单(亿)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topBoards.map((stock: any, i: number) => (
                          <tr key={stock.symbol} className="border-b border-border hover:bg-muted transition-colors">
                            <td className="px-3 py-2 text-muted-foreground font-mono">{i + 1}</td>
                            <td className="px-3 py-2 font-mono">{stock.symbol}</td>
                            <td className="px-3 py-2">
                              <button onClick={() => router.push(`/stock?symbol=${stock.symbol}`)} className="hover:text-primary transition-colors">
                                {stock.name}
                              </button>
                            </td>
                            <td className="px-3 py-2 text-right font-mono">
                              <span className="text-up font-semibold">{stock.boards}</span>
                            </td>
                            <td className="px-3 py-2 text-muted-foreground">{stock.industry || '--'}</td>
                            <td className="px-3 py-2 text-right font-mono">{stock.fengdan?.toFixed(2) || '--'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 板块资金流向 */}
            {sectorFlow.length > 0 && (
              <Card className="border-border rounded">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-muted-foreground" />
                    <CardTitle className="text-sm">板块资金流向</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">#</th>
                          <th className="text-left px-3 py-2 text-muted-foreground font-medium">板块</th>
                          <th className="text-right px-3 py-2 text-muted-foreground font-medium">涨跌幅</th>
                          <th className="text-right px-3 py-2 text-muted-foreground font-medium">主力净流入</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sectorFlow.slice(0, 10).map((s: any, i: number) => (
                          <tr key={i} className="border-b border-border hover:bg-muted transition-colors">
                            <td className="px-3 py-2 text-muted-foreground font-mono">{i + 1}</td>
                            <td className="px-3 py-2">{s['名称'] || '--'}</td>
                            <td className={`px-3 py-2 text-right font-mono ${parseFloat(s['今日涨跌幅'] || 0) >= 0 ? 'text-up' : 'text-down'}`}>
                              {s['今日涨跌幅'] ? `${parseFloat(s['今日涨跌幅']).toFixed(2)}%` : '--'}
                            </td>
                            <td className={`px-3 py-2 text-right font-mono ${parseFloat(s['主力净流入-净额'] || 0) >= 0 ? 'text-up' : 'text-down'}`}>
                              {s['主力净流入-净额'] ? `${(parseFloat(s['主力净流入-净额']) / 1e8).toFixed(2)}亿` : '--'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
